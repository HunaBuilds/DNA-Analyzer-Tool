INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
smDefDetail         BYTE "similarity_detail.txt", 0
smStatus            BYTE "STATUS=OK", 13, 10, "OPERATION=SIMILARITY", 13, 10, "COMPARISON=Positional Similarity", 13, 10, "SEQ1_HEADER=", 0
smSeq1Len           BYTE 13, 10, "SEQ1_LENGTH=", 0
smSeq2Hdr           BYTE 13, 10, "SEQ2_HEADER=", 0
smSeq2Len           BYTE 13, 10, "SEQ2_LENGTH=", 0
smMatches           BYTE 13, 10, "MATCH_COUNT=", 0
smMismatches        BYTE 13, 10, "MISMATCH_COUNT=", 0
smUnpaired          BYTE 13, 10, "UNPAIRED_COUNT=", 0
smCompared          BYTE 13, 10, "COMPARED_POSITIONS=", 0
smPercent           BYTE 13, 10, "SIMILARITY_PERCENT=", 0
smLonger            BYTE 13, 10, "LONGER_SEQUENCE=", 0
smDetailLbl         BYTE 13, 10, "DETAIL_PATH=", 0
smEnd               BYTE 13, 10, 0
smNone              BYTE "NONE", 0
smOne               BYTE "1", 0
smTwo               BYTE "2", 0
smTagMatch          BYTE "ROW|MATCH|", 0
smTagMis            BYTE "ROW|MISMATCH|", 0
smTagUnp            BYTE "ROW|UNPAIRED|", 0
smPipe              BYTE "|", 0

.code

CompareSequences PROC USES ebx esi edi, pCtx:DWORD
    LOCAL hDetail:DWORD
    LOCAL hReport:DWORD
    LOCAL len1:DWORD
    LOCAL len2:DWORD
    LOCAL compared:DWORD
    LOCAL matchCount:DWORD
    LOCAL mismatchCount:DWORD
    LOCAL unpairedCount:DWORD
    LOCAL pos:DWORD
    LOCAL longerId:DWORD
    LOCAL base1:BYTE
    LOCAL base2:BYTE

    mov hDetail, 0
    mov hReport, 0
    mov matchCount, 0
    mov mismatchCount, 0
    mov unpairedCount, 0
    mov longerId, 0

    mov ebx, pCtx
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).inPath2[0], 0
    jne sm_have_in2
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_SECOND_FILE
    xor eax, eax
    ret

sm_have_in2:
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).detailPath[0], 0
    jne sm_detail_ready
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke CopyZString, eax, ADDR smDefDetail, MAX_PATH_LEN

sm_detail_ready:
    mov ebx, pCtx
    invoke LoadSecondFasta, ebx
    test eax, eax
    jnz sm_both_loaded
    xor eax, eax
    ret

sm_both_loaded:
    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov len1, eax
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen2
    mov len2, eax
    cmp len1, 0
    je sm_unavail
    cmp len2, 0
    je sm_unavail

    mov eax, len1
    cmp eax, len2
    jbe sm_len1_shorter
    mov eax, len2
    mov longerId, 1
    jmp sm_set_compared
sm_len1_shorter:
    cmp eax, len2
    je sm_equal_len
    mov longerId, 2
sm_equal_len:
sm_set_compared:
    mov compared, eax

    lea edx, (SESSION_CTX PTR [ebx]).detailPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je sm_fail_write
    mov hDetail, eax

    mov pos, 0
sm_cmp_loop:
    mov eax, pos
    cmp eax, compared
    jae sm_cmp_done

    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    add esi, pos
    mov edi, (SESSION_CTX PTR [ebx]).pCleanSeq2
    add edi, pos
    mov al, [esi]
    mov dl, [edi]
    mov base1, al
    mov base2, dl
    cmp al, dl
    jne sm_write_mis

    inc matchCount
    invoke WriteFileZStr, hDetail, ADDR smTagMatch
    jmp sm_write_pair

sm_write_mis:
    inc mismatchCount
    invoke WriteFileZStr, hDetail, ADDR smTagMis

sm_write_pair:
    mov eax, pos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR smPipe
    invoke WriteFileBytes, hDetail, ADDR base1, 1
    invoke WriteFileZStr, hDetail, ADDR smPipe
    invoke WriteFileBytes, hDetail, ADDR base2, 1
    invoke WriteFileCrlf, hDetail
    inc pos
    jmp sm_cmp_loop

sm_cmp_done:
    cmp longerId, 1
    je sm_tail1
    cmp longerId, 2
    je sm_tail2
    jmp sm_tail_done

sm_tail1:
    mov eax, len1
    sub eax, compared
    mov unpairedCount, eax
    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    add esi, compared
    mov pos, 0
sm_tail1_loop:
    mov eax, pos
    cmp eax, unpairedCount
    jae sm_tail_done
    invoke WriteFileZStr, hDetail, ADDR smTagUnp
    mov eax, compared
    add eax, pos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR smPipe
    invoke WriteFileZStr, hDetail, ADDR smOne
    invoke WriteFileZStr, hDetail, ADDR smPipe
    invoke WriteFileBytes, hDetail, esi, 1
    invoke WriteFileCrlf, hDetail
    inc esi
    inc pos
    jmp sm_tail1_loop

sm_tail2:
    mov eax, len2
    sub eax, compared
    mov unpairedCount, eax
    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq2
    add esi, compared
    mov pos, 0
sm_tail2_loop:
    mov eax, pos
    cmp eax, unpairedCount
    jae sm_tail_done
    invoke WriteFileZStr, hDetail, ADDR smTagUnp
    mov eax, compared
    add eax, pos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR smPipe
    invoke WriteFileZStr, hDetail, ADDR smTwo
    invoke WriteFileZStr, hDetail, ADDR smPipe
    invoke WriteFileBytes, hDetail, esi, 1
    invoke WriteFileCrlf, hDetail
    inc esi
    inc pos
    jmp sm_tail2_loop

sm_tail_done:
    mov eax, hDetail
    call CloseFile
    mov hDetail, 0

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je sm_fail_write
    mov hReport, eax

    invoke WriteFileZStr, hReport, ADDR smStatus
    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).pHeaderBuf
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR smSeq1Len
    invoke WriteFileUInt32, hReport, len1
    invoke WriteFileZStr, hReport, ADDR smSeq2Hdr
    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).pHeaderBuf2
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR smSeq2Len
    invoke WriteFileUInt32, hReport, len2
    invoke WriteFileZStr, hReport, ADDR smMatches
    invoke WriteFileUInt32, hReport, matchCount
    invoke WriteFileZStr, hReport, ADDR smMismatches
    invoke WriteFileUInt32, hReport, mismatchCount
    invoke WriteFileZStr, hReport, ADDR smUnpaired
    invoke WriteFileUInt32, hReport, unpairedCount
    invoke WriteFileZStr, hReport, ADDR smCompared
    invoke WriteFileUInt32, hReport, compared
    invoke WriteFileZStr, hReport, ADDR smPercent
    invoke CalcScaledPct, matchCount, compared
    invoke WriteFileScaledPct, hReport, eax
    invoke WriteFileZStr, hReport, ADDR smLonger
    cmp longerId, 1
    je sm_write_longer1
    cmp longerId, 2
    je sm_write_longer2
    invoke WriteFileZStr, hReport, ADDR smNone
    jmp sm_after_longer
sm_write_longer1:
    invoke WriteFileZStr, hReport, ADDR smOne
    jmp sm_after_longer
sm_write_longer2:
    invoke WriteFileZStr, hReport, ADDR smTwo
sm_after_longer:
    invoke WriteFileZStr, hReport, ADDR smDetailLbl
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR smEnd

    mov eax, hReport
    call CloseFile
    mov eax, 1
    ret

sm_unavail:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_COMPARE_UNAVAILABLE
    xor eax, eax
    ret

sm_fail_write:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    cmp hDetail, 0
    je sm_fail_ret
    mov eax, hDetail
    call CloseFile
sm_fail_ret:
    xor eax, eax
    ret
CompareSequences ENDP

END
