INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
lblGcHeader         BYTE "STATUS=OK", 13, 10, "OPERATION=GC_WIN", 13, 10, "WINDOW_SIZE=", 0
lblStepSize         BYTE 13, 10, "STEP_SIZE=", 0
lblTotalWin         BYTE 13, 10, "TOTAL_WINDOWS=", 0
lblWinPrefix        BYTE 13, 10, "WINDOW_", 0
strEqChar           BYTE "=", 0
strCommaChar        BYTE ",", 0
lblGcEnd            BYTE 13, 10, 0

.code

RunGcWindow PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hHeap:DWORD
    LOCAL hFile:DWORD
    LOCAL maxWindows:DWORD
    LOCAL startIdx:DWORD
    LOCAL winIdx:DWORD
    LOCAL winEnd:DWORD
    LOCAL gcCount:DWORD
    LOCAL atCount:DWORD
    LOCAL validWin:DWORD
    LOCAL scaledGC:DWORD
    LOCAL scaledAT:DWORD

    mov ebx, pCtx

    mov eax, (SESSION_CTX PTR [ebx]).winSize
    cmp eax, 0
    jle gc_invalid_params
    cmp eax, (SESSION_CTX PTR [ebx]).cleanLen
    ja gc_invalid_params

    mov edx, (SESSION_CTX PTR [ebx]).stepSize
    cmp edx, 0
    jle gc_invalid_params

    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    sub eax, (SESSION_CTX PTR [ebx]).winSize
    xor edx, edx
    div (SESSION_CTX PTR [ebx]).stepSize
    inc eax
    mov maxWindows, eax

    mov ecx, 64
    mul ecx
    add eax, 512
    mov edx, eax

    invoke GetProcessHeap
    mov hHeap, eax
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz gc_fail_mem
    mov (SESSION_CTX PTR [ebx]).pOutBuf, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblGcHeader
    mov edi, eax
    invoke WriteUInt32Cursor, edi, (SESSION_CTX PTR [ebx]).winSize
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblStepSize
    mov edi, eax
    invoke WriteUInt32Cursor, edi, (SESSION_CTX PTR [ebx]).stepSize
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblTotalWin
    mov edi, eax
    invoke WriteUInt32Cursor, edi, maxWindows
    mov edi, eax

    mov startIdx, 0
    mov winIdx, 1

window_outer_loop:
    mov eax, startIdx
    add eax, (SESSION_CTX PTR [ebx]).winSize
    cmp eax, (SESSION_CTX PTR [ebx]).cleanLen
    ja windows_done
    mov winEnd, eax

    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    add esi, startIdx
    mov ecx, (SESSION_CTX PTR [ebx]).winSize
    mov gcCount, 0
    mov atCount, 0

window_inner_loop:
    cmp ecx, 0
    je window_calc
    mov al, [esi]
    inc esi
    dec ecx

    cmp al, 'G'
    je win_inc_gc
    cmp al, 'C'
    je win_inc_gc
    cmp al, 'A'
    je win_inc_at
    cmp al, 'T'
    je win_inc_at
    jmp window_inner_loop

win_inc_gc:
    inc gcCount
    jmp window_inner_loop

win_inc_at:
    inc atCount
    jmp window_inner_loop

window_calc:
    mov eax, gcCount
    add eax, atCount
    mov validWin, eax

    invoke CalcScaledPct, gcCount, validWin
    mov scaledGC, eax

    invoke CalcScaledPct, atCount, validWin
    mov scaledAT, eax

    invoke WriteZStrCursor, edi, ADDR lblWinPrefix
    mov edi, eax
    invoke WriteUInt32Cursor, edi, winIdx
    mov edi, eax
    invoke WriteZStrCursor, edi, ADDR strEqChar
    mov edi, eax

    mov eax, startIdx
    inc eax
    invoke WriteUInt32Cursor, edi, eax
    mov edi, eax
    invoke WriteZStrCursor, edi, ADDR strCommaChar
    mov edi, eax

    invoke WriteUInt32Cursor, edi, winEnd
    mov edi, eax
    invoke WriteZStrCursor, edi, ADDR strCommaChar
    mov edi, eax

    invoke WriteUInt32Cursor, edi, gcCount
    mov edi, eax
    invoke WriteZStrCursor, edi, ADDR strCommaChar
    mov edi, eax

    invoke WriteScaledPctCursor, edi, scaledGC
    mov edi, eax
    invoke WriteZStrCursor, edi, ADDR strCommaChar
    mov edi, eax

    invoke WriteScaledPctCursor, edi, scaledAT
    mov edi, eax

    inc winIdx
    mov eax, startIdx
    add eax, (SESSION_CTX PTR [ebx]).stepSize
    mov startIdx, eax
    jmp window_outer_loop

windows_done:
    invoke WriteZStrCursor, edi, ADDR lblGcEnd
    mov edi, eax

    sub edi, (SESSION_CTX PTR [ebx]).pOutBuf
    mov (SESSION_CTX PTR [ebx]).outLen, edi

    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je gc_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    mov ecx, (SESSION_CTX PTR [ebx]).outLen
    call WriteToFile

    mov eax, hFile
    call CloseFile

    mov eax, 1
    ret

gc_invalid_params:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_PARAMS
    xor eax, eax
    ret

gc_fail_mem:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret

gc_fail_write:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    xor eax, eax
    ret
RunGcWindow ENDP

END
