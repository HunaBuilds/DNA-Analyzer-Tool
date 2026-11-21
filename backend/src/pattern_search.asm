INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
psDefDetail         BYTE "pattern_detail.txt", 0
psStatus            BYTE "STATUS=OK", 13, 10, "OPERATION=PATTERN", 13, 10, "PATTERN=", 0
psPatLen            BYTE 13, 10, "PATTERN_LENGTH=", 0
psMatchCnt          BYTE 13, 10, "MATCH_COUNT=", 0
psDetailLbl         BYTE 13, 10, "DETAIL_PATH=", 0
psEnd               BYTE 13, 10, 0
psMatchTag          BYTE "MATCH|", 0
psPipe              BYTE "|", 0

.code

SearchDnaPattern PROC USES ebx esi edi, pCtx:DWORD
    LOCAL hDetail:DWORD
    LOCAL hReport:DWORD
    LOCAL patLen:DWORD
    LOCAL seqLen:DWORD
    LOCAL startPos:DWORD
    LOCAL matchCount:DWORD

    mov ebx, pCtx
    mov hDetail, 0
    mov hReport, 0
    mov matchCount, 0

    cmp BYTE PTR (SESSION_CTX PTR [ebx]).detailPath[0], 0
    jne ps_detail_ready
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke CopyZString, eax, ADDR psDefDetail, MAX_PATH_LEN

ps_detail_ready:
    mov ebx, pCtx
    lea esi, (SESSION_CTX PTR [ebx]).patternBuf
    xor ecx, ecx

ps_norm:
    mov al, [esi]
    cmp al, 0
    je ps_norm_done
    cmp al, 'a'
    jb ps_check
    cmp al, 'z'
    ja ps_check
    sub al, 20h
    mov [esi], al
ps_check:
    cmp al, 'A'
    je ps_okch
    cmp al, 'T'
    je ps_okch
    cmp al, 'G'
    je ps_okch
    cmp al, 'C'
    je ps_okch
    cmp al, 'N'
    je ps_okch
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_PATTERN
    inc ecx
    mov (SESSION_CTX PTR [ebx]).errPos, ecx
    xor eax, eax
    ret
ps_okch:
    inc esi
    inc ecx
    jmp ps_norm

ps_norm_done:
    mov patLen, ecx
    cmp ecx, 0
    jne ps_open_detail
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_EMPTY_PATTERN
    xor eax, eax
    ret

ps_open_detail:
    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov seqLen, eax
    lea edx, (SESSION_CTX PTR [ebx]).detailPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je ps_fail_write
    mov hDetail, eax

    mov startPos, 0

ps_scan:
    mov eax, startPos
    add eax, patLen
    cmp eax, seqLen
    ja ps_scan_done

    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    add esi, startPos
    lea edi, (SESSION_CTX PTR [ebx]).patternBuf
    mov ecx, patLen

ps_cmp:
    cmp ecx, 0
    je ps_hit
    mov al, [esi]
    mov dl, [edi]
    cmp al, dl
    jne ps_advance
    inc esi
    inc edi
    dec ecx
    jmp ps_cmp

ps_hit:
    inc matchCount
    invoke WriteFileZStr, hDetail, ADDR psMatchTag
    invoke WriteFileUInt32, hDetail, matchCount
    invoke WriteFileZStr, hDetail, ADDR psPipe
    mov eax, startPos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR psPipe
    mov eax, startPos
    add eax, patLen
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR psPipe
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).patternBuf
    invoke WriteFileZStr, hDetail, eax
    invoke WriteFileCrlf, hDetail

ps_advance:
    inc startPos
    jmp ps_scan

ps_scan_done:
    mov eax, hDetail
    call CloseFile
    mov hDetail, 0

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je ps_fail_write
    mov hReport, eax

    invoke WriteFileZStr, hReport, ADDR psStatus
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).patternBuf
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR psPatLen
    invoke WriteFileUInt32, hReport, patLen
    invoke WriteFileZStr, hReport, ADDR psMatchCnt
    invoke WriteFileUInt32, hReport, matchCount
    invoke WriteFileZStr, hReport, ADDR psDetailLbl
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR psEnd

    mov eax, hReport
    call CloseFile
    mov hReport, 0

    mov eax, 1
    ret

ps_fail_write:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    cmp hDetail, 0
    je ps_fail_ret
    mov eax, hDetail
    call CloseFile
ps_fail_ret:
    xor eax, eax
    ret
SearchDnaPattern ENDP

END
