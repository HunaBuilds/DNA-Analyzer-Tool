INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

GetFileSize PROTO, hFile:DWORD, lpFileSizeHigh:PTR DWORD

.code

LoadAndParseFasta PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hFile:DWORD
    LOCAL hHeap:DWORD
    LOCAL fileSize:DWORD
    LOCAL bytesRead:DWORD
    LOCAL parseState:DWORD
    LOCAL hdrPtr:DWORD
    LOCAL hdrCount:DWORD
    LOCAL seqCount:DWORD

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).inPath
    call OpenInputFile
    cmp eax, INVALID_HANDLE_VALUE
    je fail_open
    mov hFile, eax

    invoke GetFileSize, hFile, 0
    cmp eax, 0FFFFFFFFh
    je fail_empty_close
    cmp eax, 0
    je fail_empty_close
    mov fileSize, eax
    mov (SESSION_CTX PTR [ebx]).rawBytes, eax

    invoke GetProcessHeap
    mov hHeap, eax

    mov edx, fileSize
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz fail_mem_close
    mov (SESSION_CTX PTR [ebx]).pRawBuf, eax

    mov edx, fileSize
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz fail_mem_close
    mov (SESSION_CTX PTR [ebx]).pCleanSeq, eax

    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, MAX_HEADER_LEN
    test eax, eax
    jz fail_mem_close
    mov (SESSION_CTX PTR [ebx]).pHeaderBuf, eax
    mov hdrPtr, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pRawBuf
    mov ecx, fileSize
    call ReadFromFile
    mov bytesRead, eax

    mov eax, hFile
    call CloseFile

    mov esi, (SESSION_CTX PTR [ebx]).pRawBuf
    mov edi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov ecx, bytesRead
    xor edx, edx
    mov parseState, 0
    mov hdrCount, 0
    mov seqCount, 0

parse_loop:
    cmp ecx, 0
    je parse_finished
    mov al, [esi]
    inc esi
    dec ecx
    inc edx

    mov eax, parseState
    cmp eax, 0
    je state_expect_header
    cmp eax, 1
    je state_read_header
    jmp state_read_seq

state_expect_header:
    mov al, [esi - 1]
    cmp al, ASCII_SPACE
    je parse_loop
    cmp al, ASCII_TAB
    je parse_loop
    cmp al, ASCII_CR
    je parse_loop
    cmp al, ASCII_LF
    je parse_loop
    cmp al, ASCII_GT
    jne fail_no_header
    mov parseState, 1
    jmp parse_loop

state_read_header:
    mov al, [esi - 1]
    cmp al, ASCII_LF
    je finish_header_line
    cmp al, ASCII_CR
    je parse_loop
    push ecx
    mov ecx, hdrCount
    cmp ecx, MAX_HEADER_LEN - 1
    pop ecx
    jge parse_loop
    push edi
    mov edi, hdrPtr
    mov [edi], al
    inc edi
    mov hdrPtr, edi
    pop edi
    inc hdrCount
    jmp parse_loop

finish_header_line:
    push edi
    mov edi, hdrPtr
    mov BYTE PTR [edi], 0
    pop edi
    mov eax, hdrCount
    mov (SESSION_CTX PTR [ebx]).headerLen, eax
    mov parseState, 2
    jmp parse_loop

state_read_seq:
    mov al, [esi - 1]
    cmp al, ASCII_GT
    je parse_finished
    cmp al, ASCII_SPACE
    je parse_loop
    cmp al, ASCII_TAB
    je parse_loop
    cmp al, ASCII_CR
    je parse_loop
    cmp al, ASCII_LF
    je parse_loop

    cmp al, 'a'
    jb validate_base
    cmp al, 'z'
    ja validate_base
    sub al, 20h

validate_base:
    cmp al, 'A'
    je accept_base
    cmp al, 'T'
    je accept_base
    cmp al, 'G'
    je accept_base
    cmp al, 'C'
    je accept_base
    cmp al, 'N'
    je accept_base

    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_CHAR
    mov (SESSION_CTX PTR [ebx]).errPos, edx
    xor eax, eax
    ret

accept_base:
    mov [edi], al
    inc edi
    inc seqCount
    jmp parse_loop

parse_finished:
    mov BYTE PTR [edi], 0
    mov eax, seqCount
    mov (SESSION_CTX PTR [ebx]).cleanLen, eax
    cmp eax, 0
    je fail_empty_seq
    mov eax, 1
    ret

fail_open:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_OPEN
    xor eax, eax
    ret

fail_empty_close:
    mov eax, hFile
    call CloseFile
fail_empty_seq:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_EMPTY_SEQ
    xor eax, eax
    ret

fail_mem_close:
    mov eax, hFile
    call CloseFile
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret

fail_no_header:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_NO_HEADER
    mov (SESSION_CTX PTR [ebx]).errPos, edx
    xor eax, eax
    ret
LoadAndParseFasta ENDP

LoadRawSequence PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hFile:DWORD
    LOCAL hHeap:DWORD
    LOCAL fileSize:DWORD
    LOCAL bytesRead:DWORD
    LOCAL seqCount:DWORD

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).inPath
    call OpenInputFile
    cmp eax, INVALID_HANDLE_VALUE
    je raw_fail_open
    mov hFile, eax

    invoke GetFileSize, hFile, 0
    cmp eax, 0FFFFFFFFh
    je raw_fail_empty
    cmp eax, 0
    je raw_fail_empty
    mov fileSize, eax

    invoke GetProcessHeap
    mov hHeap, eax
    mov edx, fileSize
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz raw_fail_mem
    mov (SESSION_CTX PTR [ebx]).pRawBuf, eax

    mov edx, fileSize
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz raw_fail_mem
    mov (SESSION_CTX PTR [ebx]).pCleanSeq, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pRawBuf
    mov ecx, fileSize
    call ReadFromFile
    mov bytesRead, eax

    mov eax, hFile
    call CloseFile

    mov esi, (SESSION_CTX PTR [ebx]).pRawBuf
    mov edi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov ecx, bytesRead
    xor edx, edx
    mov seqCount, 0

raw_scan:
    cmp ecx, 0
    je raw_done
    mov al, [esi]
    inc esi
    dec ecx
    inc edx
    cmp al, ASCII_SPACE
    je raw_scan
    cmp al, ASCII_TAB
    je raw_scan
    cmp al, ASCII_CR
    je raw_scan
    cmp al, ASCII_LF
    je raw_scan

    cmp al, 'a'
    jb raw_chk
    cmp al, 'z'
    ja raw_chk
    sub al, 20h

raw_chk:
    cmp al, 'A'
    je raw_ok
    cmp al, 'T'
    je raw_ok
    cmp al, 'G'
    je raw_ok
    cmp al, 'C'
    je raw_ok
    cmp al, 'N'
    je raw_ok

    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_CHAR
    mov (SESSION_CTX PTR [ebx]).errPos, edx
    xor eax, eax
    ret

raw_ok:
    mov [edi], al
    inc edi
    inc seqCount
    jmp raw_scan

raw_done:
    mov BYTE PTR [edi], 0
    mov eax, seqCount
    mov (SESSION_CTX PTR [ebx]).cleanLen, eax
    cmp eax, 0
    je raw_fail_empty_seq
    mov eax, 1
    ret

raw_fail_open:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_OPEN
    xor eax, eax
    ret

raw_fail_empty:
    mov eax, hFile
    call CloseFile
raw_fail_empty_seq:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_EMPTY_SEQ
    xor eax, eax
    ret

raw_fail_mem:
    mov eax, hFile
    call CloseFile
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret
LoadRawSequence ENDP

LoadSecondFasta PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hFile:DWORD
    LOCAL hHeap:DWORD
    LOCAL rawPtr:DWORD
    LOCAL rawSize:DWORD
    LOCAL bytesRead:DWORD
    LOCAL parseState:DWORD
    LOCAL hdrPtr:DWORD
    LOCAL hdrCount:DWORD
    LOCAL seqCount:DWORD
    LOCAL savedResult:DWORD

    mov ebx, pCtx
    mov rawPtr, 0
    mov hFile, 0
    mov (SESSION_CTX PTR [ebx]).pCleanSeq2, 0
    mov (SESSION_CTX PTR [ebx]).pHeaderBuf2, 0
    mov (SESSION_CTX PTR [ebx]).cleanLen2, 0
    mov (SESSION_CTX PTR [ebx]).headerLen2, 0

    lea edx, (SESSION_CTX PTR [ebx]).inPath2
    call OpenInputFile
    cmp eax, INVALID_HANDLE_VALUE
    je s2_fail_open
    mov hFile, eax

    invoke GetFileSize, hFile, 0
    cmp eax, 0FFFFFFFFh
    je s2_fail_empty_close
    cmp eax, 0
    je s2_fail_empty_close
    mov rawSize, eax

    invoke GetProcessHeap
    mov hHeap, eax

    mov edx, rawSize
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz s2_fail_mem_close
    mov rawPtr, eax

    mov edx, rawSize
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz s2_fail_mem_close
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).pCleanSeq2, eax

    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, MAX_HEADER_LEN
    test eax, eax
    jz s2_fail_mem_close
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).pHeaderBuf2, eax
    mov hdrPtr, eax

    mov eax, hFile
    mov edx, rawPtr
    mov ecx, rawSize
    call ReadFromFile
    mov bytesRead, eax

    mov eax, hFile
    call CloseFile
    mov hFile, 0

    mov ebx, pCtx
    mov esi, rawPtr
    mov edi, (SESSION_CTX PTR [ebx]).pCleanSeq2
    mov ecx, bytesRead
    xor edx, edx
    mov parseState, 0
    mov hdrCount, 0
    mov seqCount, 0

s2_parse_loop:
    cmp ecx, 0
    je s2_parse_finished
    mov al, [esi]
    inc esi
    dec ecx
    inc edx

    mov eax, parseState
    cmp eax, 0
    je s2_expect_header
    cmp eax, 1
    je s2_read_header
    jmp s2_read_seq

s2_expect_header:
    mov al, [esi - 1]
    cmp al, ASCII_SPACE
    je s2_parse_loop
    cmp al, ASCII_TAB
    je s2_parse_loop
    cmp al, ASCII_CR
    je s2_parse_loop
    cmp al, ASCII_LF
    je s2_parse_loop
    cmp al, ASCII_GT
    jne s2_fail_no_header
    mov parseState, 1
    jmp s2_parse_loop

s2_read_header:
    mov al, [esi - 1]
    cmp al, ASCII_LF
    je s2_finish_header
    cmp al, ASCII_CR
    je s2_parse_loop
    push ecx
    mov ecx, hdrCount
    cmp ecx, MAX_HEADER_LEN - 1
    pop ecx
    jge s2_parse_loop
    push edi
    mov edi, hdrPtr
    mov [edi], al
    inc edi
    mov hdrPtr, edi
    pop edi
    inc hdrCount
    jmp s2_parse_loop

s2_finish_header:
    push edi
    mov edi, hdrPtr
    mov BYTE PTR [edi], 0
    pop edi
    mov eax, hdrCount
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).headerLen2, eax
    mov parseState, 2
    jmp s2_parse_loop

s2_read_seq:
    mov al, [esi - 1]
    cmp al, ASCII_GT
    je s2_parse_finished
    cmp al, ASCII_SPACE
    je s2_parse_loop
    cmp al, ASCII_TAB
    je s2_parse_loop
    cmp al, ASCII_CR
    je s2_parse_loop
    cmp al, ASCII_LF
    je s2_parse_loop

    cmp al, 'a'
    jb s2_validate
    cmp al, 'z'
    ja s2_validate
    sub al, 20h

s2_validate:
    cmp al, 'A'
    je s2_accept
    cmp al, 'T'
    je s2_accept
    cmp al, 'G'
    je s2_accept
    cmp al, 'C'
    je s2_accept
    cmp al, 'N'
    je s2_accept
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_CHAR
    mov (SESSION_CTX PTR [ebx]).errPos, edx
    jmp s2_fail

s2_accept:
    mov [edi], al
    inc edi
    inc seqCount
    jmp s2_parse_loop

s2_parse_finished:
    mov BYTE PTR [edi], 0
    mov eax, seqCount
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).cleanLen2, eax
    cmp eax, 0
    je s2_fail_empty_seq
    mov eax, 1
    jmp s2_epilogue

s2_fail_open:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_SECOND_FILE
    xor eax, eax
    ret

s2_fail_empty_close:
    mov eax, hFile
    call CloseFile
    mov hFile, 0
s2_fail_empty_seq:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_EMPTY_SEQ
    jmp s2_fail

s2_fail_mem_close:
    cmp hFile, 0
    je s2_mem_set
    mov eax, hFile
    call CloseFile
    mov hFile, 0
s2_mem_set:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    jmp s2_fail

s2_fail_no_header:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_NO_HEADER
    mov (SESSION_CTX PTR [ebx]).errPos, edx
    jmp s2_fail

s2_fail:
    xor eax, eax

s2_epilogue:
    mov savedResult, eax
    cmp rawPtr, 0
    je s2_done
    invoke GetProcessHeap
    mov hHeap, eax
    invoke HeapFree, hHeap, 0, rawPtr
    mov rawPtr, 0
s2_done:
    mov eax, savedResult
    ret
LoadSecondFasta ENDP

END
