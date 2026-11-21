INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
ptDefDetail         BYTE "primer_detail.txt", 0
ptStatus            BYTE "STATUS=OK", 13, 10, "OPERATION=PRIMER_TM", 13, 10, "ESTIMATE=Basic Wallace-rule Tm estimate", 13, 10, "CANDIDATE_LENGTH=", 0
ptTotal             BYTE 13, 10, "TOTAL_WINDOWS=", 0
ptValid             BYTE 13, 10, "VALID_CANDIDATES=", 0
ptAmb               BYTE 13, 10, "AMBIGUOUS_WINDOWS=", 0
ptMin               BYTE 13, 10, "MIN_TM=", 0
ptMax               BYTE 13, 10, "MAX_TM=", 0
ptAvg               BYTE 13, 10, "AVERAGE_TM=", 0
ptDetailLbl         BYTE 13, 10, "DETAIL_PATH=", 0
ptEnd               BYTE 13, 10, 0
ptUnavail           BYTE "UNAVAILABLE", 0
ptCand              BYTE "CAND|", 0
ptPipe              BYTE "|", 0
ptDot               BYTE ".", 0
ptZero              BYTE "0", 0

.code

ScanPrimerTm PROC USES ebx esi edi, pCtx:DWORD
    LOCAL hDetail:DWORD
    LOCAL hReport:DWORD
    LOCAL seqLen:DWORD
    LOCAL winLen:DWORD
    LOCAL startPos:DWORD
    LOCAL totalWin:DWORD
    LOCAL validCount:DWORD
    LOCAL ambCount:DWORD
    LOCAL candNum:DWORD
    LOCAL countA:DWORD
    LOCAL countT:DWORD
    LOCAL countG:DWORD
    LOCAL countC:DWORD
    LOCAL countN:DWORD
    LOCAL tmVal:DWORD
    LOCAL minTm:DWORD
    LOCAL maxTm:DWORD
    LOCAL sumLo:DWORD
    LOCAL sumHi:DWORD
    LOCAL intPart:DWORD
    LOCAL fracPart:DWORD

    mov hDetail, 0
    mov hReport, 0
    mov totalWin, 0
    mov validCount, 0
    mov ambCount, 0
    mov candNum, 0
    mov sumLo, 0
    mov sumHi, 0
    mov minTm, 0
    mov maxTm, 0

    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov seqLen, eax
    mov eax, (SESSION_CTX PTR [ebx]).winSize
    mov winLen, eax
    cmp eax, 1
    jb pt_bad_len
    cmp eax, seqLen
    ja pt_bad_len

    cmp BYTE PTR (SESSION_CTX PTR [ebx]).detailPath[0], 0
    jne pt_detail_ready
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke CopyZString, eax, ADDR ptDefDetail, MAX_PATH_LEN

pt_detail_ready:
    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).detailPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je pt_fail_write
    mov hDetail, eax

    mov startPos, 0

pt_win_loop:
    mov eax, startPos
    add eax, winLen
    cmp eax, seqLen
    ja pt_win_done

    inc totalWin
    mov countA, 0
    mov countT, 0
    mov countG, 0
    mov countC, 0
    mov countN, 0

    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    add esi, startPos
    mov ecx, winLen

pt_inner:
    cmp ecx, 0
    je pt_classified
    mov al, [esi]
    inc esi
    dec ecx
    cmp al, 'A'
    je pt_inc_a
    cmp al, 'T'
    je pt_inc_t
    cmp al, 'G'
    je pt_inc_g
    cmp al, 'C'
    je pt_inc_c
    inc countN
    jmp pt_inner
pt_inc_a:
    inc countA
    jmp pt_inner
pt_inc_t:
    inc countT
    jmp pt_inner
pt_inc_g:
    inc countG
    jmp pt_inner
pt_inc_c:
    inc countC
    jmp pt_inner

pt_classified:
    cmp countN, 0
    je pt_valid_win
    inc ambCount
    jmp pt_next_win

pt_valid_win:
    mov eax, countA
    add eax, countT
    shl eax, 1
    mov edx, countG
    add edx, countC
    shl edx, 2
    add eax, edx
    mov tmVal, eax

    inc candNum
    mov edx, candNum
    mov validCount, edx
    cmp candNum, 1
    jne pt_minmax
    mov minTm, eax
    mov maxTm, eax
    jmp pt_add_sum
pt_minmax:
    cmp eax, minTm
    jae pt_check_max
    mov minTm, eax
pt_check_max:
    cmp eax, maxTm
    jbe pt_add_sum
    mov maxTm, eax
pt_add_sum:
    add sumLo, eax
    adc sumHi, 0

    invoke WriteFileZStr, hDetail, ADDR ptCand
    invoke WriteFileUInt32, hDetail, candNum
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    mov eax, startPos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    mov eax, startPos
    add eax, winLen
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    invoke WriteFileUInt32, hDetail, countA
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    invoke WriteFileUInt32, hDetail, countT
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    invoke WriteFileUInt32, hDetail, countG
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    invoke WriteFileUInt32, hDetail, countC
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    invoke WriteFileUInt32, hDetail, tmVal
    invoke WriteFileZStr, hDetail, ADDR ptPipe
    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).pCleanSeq
    add eax, startPos
    invoke WriteFileBytes, hDetail, eax, winLen
    invoke WriteFileCrlf, hDetail

pt_next_win:
    inc startPos
    jmp pt_win_loop

pt_win_done:
    mov eax, hDetail
    call CloseFile
    mov hDetail, 0

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je pt_fail_write
    mov hReport, eax

    invoke WriteFileZStr, hReport, ADDR ptStatus
    invoke WriteFileUInt32, hReport, winLen
    invoke WriteFileZStr, hReport, ADDR ptTotal
    invoke WriteFileUInt32, hReport, totalWin
    invoke WriteFileZStr, hReport, ADDR ptValid
    invoke WriteFileUInt32, hReport, validCount
    invoke WriteFileZStr, hReport, ADDR ptAmb
    invoke WriteFileUInt32, hReport, ambCount
    invoke WriteFileZStr, hReport, ADDR ptMin
    cmp validCount, 0
    je pt_min_unavail
    invoke WriteFileUInt32, hReport, minTm
    jmp pt_after_min
pt_min_unavail:
    invoke WriteFileZStr, hReport, ADDR ptUnavail
pt_after_min:
    invoke WriteFileZStr, hReport, ADDR ptMax
    cmp validCount, 0
    je pt_max_unavail
    invoke WriteFileUInt32, hReport, maxTm
    jmp pt_after_max
pt_max_unavail:
    invoke WriteFileZStr, hReport, ADDR ptUnavail
pt_after_max:
    invoke WriteFileZStr, hReport, ADDR ptAvg
    cmp validCount, 0
    je pt_avg_unavail

    mov edx, sumHi
    mov eax, sumLo
    mov ebx, validCount
    div ebx
    mov intPart, eax
    mov eax, edx
    xor edx, edx
    mov ebx, 100
    mul ebx
    mov ebx, validCount
    div ebx
    mov fracPart, eax

    invoke WriteFileUInt32, hReport, intPart
    invoke WriteFileZStr, hReport, ADDR ptDot
    cmp fracPart, 10
    jae pt_frac_digits
    invoke WriteFileZStr, hReport, ADDR ptZero
pt_frac_digits:
    invoke WriteFileUInt32, hReport, fracPart
    jmp pt_after_avg

pt_avg_unavail:
    invoke WriteFileZStr, hReport, ADDR ptUnavail

pt_after_avg:
    invoke WriteFileZStr, hReport, ADDR ptDetailLbl
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR ptEnd

    mov eax, hReport
    call CloseFile
    mov eax, 1
    ret

pt_bad_len:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_LENGTH
    xor eax, eax
    ret

pt_fail_write:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    cmp hDetail, 0
    je pt_fail_ret
    mov eax, hDetail
    call CloseFile
pt_fail_ret:
    xor eax, eax
    ret
ScanPrimerTm ENDP

END
