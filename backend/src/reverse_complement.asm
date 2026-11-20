INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
defaultRcSeqPath    BYTE "reverse_complement.seq", 0
lblRcHeader         BYTE "STATUS=OK", 13, 10, "OPERATION=REVERSE_COMPLEMENT", 13, 10, "SEQUENCE_LENGTH=", 0
lblRcOutPath        BYTE 13, 10, "OUTPUT_SEQ_PATH=", 0
lblRcEnd            BYTE 13, 10, 0

.code

ComputeReverseComplement PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hHeap:DWORD
    LOCAL hFile:DWORD
    LOCAL seqLen:DWORD

    mov ebx, pCtx

    cmp BYTE PTR (SESSION_CTX PTR [ebx]).seqOutPath[0], 0
    jne rc_path_ready
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke CopyZString, eax, ADDR defaultRcSeqPath, MAX_PATH_LEN

rc_path_ready:
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov seqLen, eax

    invoke GetProcessHeap
    mov hHeap, eax
    mov edx, seqLen
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz rc_fail_mem
    mov (SESSION_CTX PTR [ebx]).pOutBuf, eax

    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    add esi, seqLen
    dec esi
    mov edi, eax
    mov ecx, seqLen

rc_loop:
    cmp ecx, 0
    je rc_loop_done
    mov al, [esi]
    dec esi
    dec ecx

    cmp al, 'A'
    je map_to_t
    cmp al, 'T'
    je map_to_a
    cmp al, 'G'
    je map_to_c
    cmp al, 'C'
    je map_to_g
    jmp store_rc_base

map_to_t:
    mov al, 'T'
    jmp store_rc_base

map_to_a:
    mov al, 'A'
    jmp store_rc_base

map_to_c:
    mov al, 'C'
    jmp store_rc_base

map_to_g:
    mov al, 'G'

store_rc_base:
    mov [edi], al
    inc edi
    jmp rc_loop

rc_loop_done:
    mov BYTE PTR [edi], 0

    lea edx, (SESSION_CTX PTR [ebx]).seqOutPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je rc_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    mov ecx, seqLen
    call WriteToFile

    mov eax, hFile
    call CloseFile

    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, 2048
    test eax, eax
    jz rc_fail_mem
    mov esi, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRcHeader
    mov edi, eax
    invoke WriteUInt32Cursor, edi, seqLen
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRcOutPath
    mov edi, eax
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke WriteZStrCursor, edi, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRcEnd
    mov edi, eax
    sub edi, esi

    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je rc_free_rep_fail
    mov hFile, eax

    mov eax, hFile
    mov edx, esi
    mov ecx, edi
    call WriteToFile

    mov eax, hFile
    call CloseFile

    invoke HeapFree, hHeap, 0, esi
    mov eax, 1
    ret

rc_free_rep_fail:
    invoke HeapFree, hHeap, 0, esi
rc_fail_write:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    xor eax, eax
    ret

rc_fail_mem:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret
ComputeReverseComplement ENDP

END
