INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
lblStatsHeader      BYTE "STATUS=OK", 13, 10, "OPERATION=STATS", 13, 10, "HEADER=", 0
lblCleanPath        BYTE 13, 10, "CLEAN_SEQ_PATH=", 0
lblSeqLen           BYTE 13, 10, "SEQUENCE_LENGTH=", 0
lblValidCanon       BYTE 13, 10, "VALID_CANONICAL=", 0
lblCountA           BYTE 13, 10, "COUNT_A=", 0
lblCountT           BYTE 13, 10, "COUNT_T=", 0
lblCountG           BYTE 13, 10, "COUNT_G=", 0
lblCountC           BYTE 13, 10, "COUNT_C=", 0
lblCountN           BYTE 13, 10, "COUNT_N=", 0
lblPctA             BYTE 13, 10, "PCT_A=", 0
lblPctT             BYTE 13, 10, "PCT_T=", 0
lblPctG             BYTE 13, 10, "PCT_G=", 0
lblPctC             BYTE 13, 10, "PCT_C=", 0
lblPctGC            BYTE 13, 10, "GC_PERCENT=", 0
lblPctAT            BYTE 13, 10, "AT_PERCENT=", 0
lblStatsEnd         BYTE 13, 10, 0
strUnknownHdr       BYTE "UNKNOWN_RECORD", 0

.code

ComputeDnaStats PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL stRes:STATS_RESULT
    LOCAL hHeap:DWORD
    LOCAL hFile:DWORD
    LOCAL gcCount:DWORD
    LOCAL atCount:DWORD

    mov ebx, pCtx

    lea edi, stRes
    mov ecx, SIZEOF STATS_RESULT
    xor al, al
    rep stosb

    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov ecx, (SESSION_CTX PTR [ebx]).cleanLen
    mov stRes.totalLen, ecx

count_loop:
    cmp ecx, 0
    je counts_done
    mov al, [esi]
    inc esi
    dec ecx

    cmp al, 'A'
    je inc_a
    cmp al, 'T'
    je inc_t
    cmp al, 'G'
    je inc_g
    cmp al, 'C'
    je inc_c
    cmp al, 'N'
    je inc_n
    jmp count_loop

inc_a:
    inc stRes.countA
    jmp count_loop

inc_t:
    inc stRes.countT
    jmp count_loop

inc_g:
    inc stRes.countG
    jmp count_loop

inc_c:
    inc stRes.countC
    jmp count_loop

inc_n:
    inc stRes.countN
    jmp count_loop

counts_done:
    mov eax, stRes.countA
    add eax, stRes.countT
    mov atCount, eax

    mov edx, stRes.countG
    add edx, stRes.countC
    mov gcCount, edx

    add eax, edx
    mov stRes.validCanonical, eax

    invoke CalcScaledPct, stRes.countA, stRes.validCanonical
    mov stRes.pctA, eax

    invoke CalcScaledPct, stRes.countT, stRes.validCanonical
    mov stRes.pctT, eax

    invoke CalcScaledPct, stRes.countG, stRes.validCanonical
    mov stRes.pctG, eax

    invoke CalcScaledPct, stRes.countC, stRes.validCanonical
    mov stRes.pctC, eax

    invoke CalcScaledPct, gcCount, stRes.validCanonical
    mov stRes.pctGC, eax

    invoke CalcScaledPct, atCount, stRes.validCanonical
    mov stRes.pctAT, eax

    cmp BYTE PTR (SESSION_CTX PTR [ebx]).cleanPath[0], 0
    je build_stats_report

    lea edx, (SESSION_CTX PTR [ebx]).cleanPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je stats_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov ecx, (SESSION_CTX PTR [ebx]).cleanLen
    call WriteToFile

    mov eax, hFile
    call CloseFile

build_stats_report:
    invoke GetProcessHeap
    mov hHeap, eax
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, 4096
    test eax, eax
    jz stats_fail_mem
    mov (SESSION_CTX PTR [ebx]).pOutBuf, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblStatsHeader
    mov edi, eax

    mov eax, (SESSION_CTX PTR [ebx]).pHeaderBuf
    test eax, eax
    jz write_default_hdr
    cmp BYTE PTR [eax], 0
    je write_default_hdr
    invoke WriteZStrCursor, edi, eax
    mov edi, eax
    jmp write_clean_line

write_default_hdr:
    invoke WriteZStrCursor, edi, ADDR strUnknownHdr
    mov edi, eax

write_clean_line:
    invoke WriteZStrCursor, edi, ADDR lblCleanPath
    mov edi, eax
    lea eax, (SESSION_CTX PTR [ebx]).cleanPath
    invoke WriteZStrCursor, edi, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblSeqLen
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.totalLen
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblValidCanon
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.validCanonical
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblCountA
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.countA
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblCountT
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.countT
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblCountG
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.countG
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblCountC
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.countC
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblCountN
    mov edi, eax
    invoke WriteUInt32Cursor, edi, stRes.countN
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPctA
    mov edi, eax
    invoke WriteScaledPctCursor, edi, stRes.pctA
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPctT
    mov edi, eax
    invoke WriteScaledPctCursor, edi, stRes.pctT
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPctG
    mov edi, eax
    invoke WriteScaledPctCursor, edi, stRes.pctG
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPctC
    mov edi, eax
    invoke WriteScaledPctCursor, edi, stRes.pctC
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPctGC
    mov edi, eax
    invoke WriteScaledPctCursor, edi, stRes.pctGC
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPctAT
    mov edi, eax
    invoke WriteScaledPctCursor, edi, stRes.pctAT
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblStatsEnd
    mov edi, eax

    sub edi, (SESSION_CTX PTR [ebx]).pOutBuf
    mov (SESSION_CTX PTR [ebx]).outLen, edi

    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je stats_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    mov ecx, (SESSION_CTX PTR [ebx]).outLen
    call WriteToFile

    mov eax, hFile
    call CloseFile

    mov eax, 1
    ret

stats_fail_mem:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret

stats_fail_write:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    xor eax, eax
    ret
ComputeDnaStats ENDP

END
