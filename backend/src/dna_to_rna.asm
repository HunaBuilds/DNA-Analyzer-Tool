INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
defaultRnaSeqPath   BYTE "transcribed_rna.seq", 0
lblRnaHeader        BYTE "STATUS=OK", 13, 10, "OPERATION=DNA_TO_RNA", 13, 10, "SEQUENCE_LENGTH=", 0
lblRnaUracil        BYTE 13, 10, "URACIL_COUNT=", 0
lblRnaOutPath       BYTE 13, 10, "OUTPUT_SEQ_PATH=", 0
lblRnaEnd           BYTE 13, 10, 0

.code

ConvertDnaToRna PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hHeap:DWORD
    LOCAL hFile:DWORD
    LOCAL seqLen:DWORD
    LOCAL uracilCount:DWORD

    mov ebx, pCtx

    cmp BYTE PTR (SESSION_CTX PTR [ebx]).seqOutPath[0], 0
    jne rna_path_ready
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke CopyZString, eax, ADDR defaultRnaSeqPath, MAX_PATH_LEN

rna_path_ready:
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov seqLen, eax

    invoke GetProcessHeap
    mov hHeap, eax
    mov edx, seqLen
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz rna_fail_mem
    mov (SESSION_CTX PTR [ebx]).pOutBuf, eax

    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov edi, eax
    mov ecx, seqLen
    mov uracilCount, 0

rna_loop:
    cmp ecx, 0
    je rna_loop_done
    mov al, [esi]
    inc esi
    dec ecx

    cmp al, 'T'
    jne store_rna_base
    mov al, 'U'
    inc uracilCount

store_rna_base:
    mov [edi], al
    inc edi
    jmp rna_loop

rna_loop_done:
    mov BYTE PTR [edi], 0

    lea edx, (SESSION_CTX PTR [ebx]).seqOutPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je rna_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    mov ecx, seqLen
    call WriteToFile

    mov eax, hFile
    call CloseFile

    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, 2048
    test eax, eax
    jz rna_fail_mem
    mov esi, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRnaHeader
    mov edi, eax
    invoke WriteUInt32Cursor, edi, seqLen
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRnaUracil
    mov edi, eax
    invoke WriteUInt32Cursor, edi, uracilCount
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRnaOutPath
    mov edi, eax
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke WriteZStrCursor, edi, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRnaEnd
    mov edi, eax
    sub edi, esi

    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je rna_free_rep_fail
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

rna_free_rep_fail:
    invoke HeapFree, hHeap, 0, esi
rna_fail_write:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    xor eax, eax
    ret

rna_fail_mem:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret
ConvertDnaToRna ENDP

END
