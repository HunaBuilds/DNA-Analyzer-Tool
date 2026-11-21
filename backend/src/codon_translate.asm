INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

GetModuleFileNameA PROTO, hModule:DWORD, lpFilename:DWORD, nSize:DWORD
GetFileSize PROTO, hFile:DWORD, lpFileSizeHigh:PTR DWORD

.data
ctDefDetail         BYTE "codon_detail.txt", 0
ctDefRna            BYTE "codon_rna.seq", 0
ctDataSuffix        BYTE "data\codon_table.csv", 0
ctHeaderLine        BYTE "codon,amino_acid_one_letter,amino_acid_name", 0
ctAmbName           BYTE "Ambiguous", 0
ctStatus            BYTE "STATUS=OK", 13, 10, "OPERATION=TRANSLATE", 13, 10, "SEQUENCE_LENGTH=", 0
ctComplete          BYTE 13, 10, "COMPLETE_CODONS=", 0
ctStop              BYTE 13, 10, "STOP_CODONS=", 0
ctAmb               BYTE 13, 10, "AMBIGUOUS_CODONS=", 0
ctLeft              BYTE 13, 10, "LEFTOVER_BASES=", 0
ctLeftSeq           BYTE 13, 10, "LEFTOVER_SEQ=", 0
ctRnaPath           BYTE 13, 10, "RNA_PATH=", 0
ctDetailLbl         BYTE 13, 10, "DETAIL_PATH=", 0
ctEnd               BYTE 13, 10, 0
ctOrd               BYTE "ORD|", 0
ctSum               BYTE "SUM|", 0
ctTrail             BYTE "TRAIL|", 0
ctPipe              BYTE "|", 0
ctSemi              BYTE ";", 0
ctModPath           BYTE MAX_PATH_LEN DUP(0)

.data?
ctBases             BYTE 500 DUP(?)
ctLetter            BYTE 250 DUP(?)
ctName              BYTE 4000 DUP(?)
ctCount             DWORD 125 DUP(?)
ctOrder             DWORD 125 DUP(?)
ctSort              DWORD 125 DUP(?)
ctSortCount         DWORD ?
ctNextOrder         DWORD ?
ctAmbNext           DWORD ?

.code

CtStrEq PROC USES esi edi, pA:DWORD, pB:DWORD
    mov esi, pA
    mov edi, pB
cteq_loop:
    mov al, [esi]
    mov ah, [edi]
    cmp al, ah
    jne cteq_no
    cmp al, 0
    je cteq_yes
    inc esi
    inc edi
    jmp cteq_loop
cteq_yes:
    mov eax, 1
    ret
cteq_no:
    xor eax, eax
    ret
CtStrEq ENDP

CtBaseValue PROC
    cmp al, 'A'
    je ctb_a
    cmp al, 'C'
    je ctb_c
    cmp al, 'G'
    je ctb_g
    cmp al, 'U'
    je ctb_u
    mov eax, 0FFFFFFFFh
    ret
ctb_a:
    xor eax, eax
    ret
ctb_c:
    mov eax, 1
    ret
ctb_g:
    mov eax, 2
    ret
ctb_u:
    mov eax, 3
    ret
CtBaseValue ENDP

ResolveCodonPath PROC USES ebx esi edi, pCtx:DWORD
    mov ebx, pCtx
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).codonPath[0], 0
    jne rcp_ok

    invoke GetModuleFileNameA, 0, ADDR ctModPath, MAX_PATH_LEN
    test eax, eax
    jz rcp_fail
    lea esi, ctModPath
    add esi, eax
    mov ecx, 2
rcp_back:
    cmp esi, OFFSET ctModPath
    jbe rcp_fail
    dec esi
    mov al, [esi]
    cmp al, '\'
    je rcp_slash
    cmp al, '/'
    jne rcp_back
rcp_slash:
    dec ecx
    jnz rcp_back
    inc esi
    lea edi, ctDataSuffix
rcp_copy:
    mov al, [edi]
    mov [esi], al
    cmp al, 0
    je rcp_store
    inc esi
    inc edi
    jmp rcp_copy
rcp_store:
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).codonPath
    invoke CopyZString, eax, ADDR ctModPath, MAX_PATH_LEN
rcp_ok:
    mov eax, 1
    ret
rcp_fail:
    xor eax, eax
    ret
ResolveCodonPath ENDP

LoadCodonTable PROC USES ebx esi edi, pCtx:DWORD
    LOCAL hFile:DWORD
    LOCAL hHeap:DWORD
    LOCAL pBuf:DWORD
    LOCAL bytesRead:DWORD
    LOCAL dataCount:DWORD
    LOCAL sawHeader:DWORD
    LOCAL c0:BYTE
    LOCAL c1:BYTE
    LOCAL c2:BYTE
    LOCAL letterCh:BYTE
    LOCAL slot:DWORD

    mov dataCount, 0
    mov sawHeader, 0
    mov pBuf, 0
    mov hFile, 0

    mov ecx, 125
    lea edi, ctCount
    xor eax, eax
    cld
lct_zero_counts:
    mov DWORD PTR [edi], 0
    add edi, 4
    dec ecx
    jnz lct_zero_counts

    mov ecx, 125
    lea edi, ctOrder
lct_zero_order:
    mov DWORD PTR [edi], 0
    add edi, 4
    dec ecx
    jnz lct_zero_order

    mov ecx, 500
    lea edi, ctBases
lct_zero_bases:
    mov BYTE PTR [edi], 0
    inc edi
    dec ecx
    jnz lct_zero_bases

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).codonPath
    call OpenInputFile
    cmp eax, INVALID_HANDLE_VALUE
    je lct_missing
    mov hFile, eax

    invoke GetFileSize, hFile, 0
    cmp eax, 0
    je lct_bad_close
    cmp eax, 0FFFFFFFFh
    je lct_bad_close
    mov ebx, eax

    invoke GetProcessHeap
    mov hHeap, eax
    mov eax, ebx
    add eax, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, eax
    test eax, eax
    jz lct_mem_close
    mov pBuf, eax

    mov eax, hFile
    mov edx, pBuf
    mov ecx, ebx
    call ReadFromFile
    mov bytesRead, eax
    mov eax, hFile
    call CloseFile
    mov hFile, 0

    mov edi, pBuf
    add edi, bytesRead
    mov BYTE PTR [edi], 0

    mov esi, pBuf
    cmp bytesRead, 3
    jb lct_no_bom
    mov al, [esi]
    cmp al, 0EFh
    jne lct_no_bom
    mov al, [esi + 1]
    cmp al, 0BBh
    jne lct_no_bom
    mov al, [esi + 2]
    cmp al, 0BFh
    jne lct_no_bom
    add esi, 3
lct_no_bom:

lct_line:
    mov al, [esi]
    cmp al, 0
    je lct_lines_done
    mov edx, esi
lct_find_eol:
    mov al, [esi]
    cmp al, 0
    je lct_have_line
    cmp al, 13
    je lct_have_line
    cmp al, 10
    je lct_have_line
    inc esi
    jmp lct_find_eol

lct_have_line:
    mov bl, al
    mov BYTE PTR [esi], 0
    cmp BYTE PTR [edx], 0
    je lct_skip_empty
    cmp sawHeader, 0
    jne lct_data_row
    invoke CtStrEq, edx, ADDR ctHeaderLine
    test eax, eax
    jz lct_bad
    mov sawHeader, 1
    jmp lct_skip_empty

lct_data_row:
    push esi
    mov esi, edx
    mov al, [esi]
    mov c0, al
    inc esi
    mov al, [esi]
    mov c1, al
    inc esi
    mov al, [esi]
    mov c2, al
    inc esi
    cmp BYTE PTR [esi], ','
    jne lct_row_bad
    inc esi
    mov al, [esi]
    cmp al, 0
    je lct_row_bad
    cmp al, ','
    je lct_row_bad
    mov letterCh, al
    inc esi
    cmp BYTE PTR [esi], ','
    jne lct_row_bad
    inc esi
    cmp BYTE PTR [esi], 0
    je lct_row_bad

    mov al, c0
    call CtBaseValue
    cmp eax, 0FFFFFFFFh
    je lct_row_bad
    mov c0, al
    mov al, c1
    call CtBaseValue
    cmp eax, 0FFFFFFFFh
    je lct_row_bad
    mov c1, al
    mov al, c2
    call CtBaseValue
    cmp eax, 0FFFFFFFFh
    je lct_row_bad
    mov c2, al

    movzx eax, c0
    shl eax, 2
    movzx edx, c1
    add eax, edx
    shl eax, 2
    movzx edx, c2
    add eax, edx
    mov slot, eax
    cmp eax, 64
    jae lct_row_bad

    shl eax, 2
    lea edi, ctBases[eax]
    cmp BYTE PTR [edi], 0
    jne lct_row_bad
    jmp lct_store_from_index

lct_row_bad:
    pop esi
    jmp lct_bad

lct_store_from_index:
    mov eax, slot
    mov edx, eax
    and edx, 3
    mov al, dl
    call CtIndexLetter
    mov [edi + 2], al
    mov eax, slot
    shr eax, 2
    mov edx, eax
    and edx, 3
    mov al, dl
    call CtIndexLetter
    mov [edi + 1], al
    mov eax, slot
    shr eax, 4
    and eax, 3
    call CtIndexLetter
    mov [edi], al
    mov BYTE PTR [edi + 3], 0

    mov eax, slot
    shl eax, 1
    lea edi, ctLetter[eax]
    mov al, letterCh
    mov [edi], al
    mov BYTE PTR [edi + 1], 0

    mov eax, slot
    shl eax, 5
    lea edi, ctName[eax]
    xor ecx, ecx
lct_name:
    mov al, [esi]
    cmp al, 0
    je lct_name_done
    cmp al, ','
    je lct_row_bad
    cmp ecx, 31
    jae lct_row_bad
    mov [edi], al
    inc edi
    inc esi
    inc ecx
    jmp lct_name
lct_name_done:
    cmp ecx, 0
    je lct_row_bad
    mov BYTE PTR [edi], 0
    pop esi
    inc dataCount

lct_skip_empty:
    cmp bl, 0
    je lct_lines_done
    inc esi
    cmp bl, 13
    jne lct_line
    cmp BYTE PTR [esi], 10
    jne lct_line
    inc esi
    jmp lct_line

lct_lines_done:
    cmp sawHeader, 1
    jne lct_bad
    cmp dataCount, 64
    jne lct_bad
    mov slot, 0
lct_verify:
    cmp slot, 64
    jae lct_verified
    mov eax, slot
    shl eax, 2
    cmp BYTE PTR ctBases[eax], 0
    je lct_bad
    inc slot
    jmp lct_verify

lct_verified:
    mov eax, pBuf
    test eax, eax
    jz lct_ok
    invoke HeapFree, hHeap, 0, eax
    mov pBuf, 0
lct_ok:
    mov eax, 1
    ret

lct_mem_close:
    mov eax, hFile
    call CloseFile
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret

lct_missing:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_CODON_MISSING
    xor eax, eax
    ret

lct_bad_close:
    mov eax, hFile
    call CloseFile
lct_bad:
    cmp pBuf, 0
    je lct_bad_set
    invoke HeapFree, hHeap, 0, pBuf
lct_bad_set:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_CODON_INVALID
    xor eax, eax
    ret
LoadCodonTable ENDP

CtIndexLetter PROC
    cmp al, 0
    jne cil1
    mov al, 'A'
    ret
cil1:
    cmp al, 1
    jne cil2
    mov al, 'C'
    ret
cil2:
    cmp al, 2
    jne cil3
    mov al, 'G'
    ret
cil3:
    mov al, 'U'
    ret
CtIndexLetter ENDP

CtContainsN PROC USES esi, pCodon:DWORD
    mov esi, pCodon
    mov al, [esi]
    cmp al, 'N'
    je ccn_yes
    mov al, [esi + 1]
    cmp al, 'N'
    je ccn_yes
    mov al, [esi + 2]
    cmp al, 'N'
    je ccn_yes
    xor eax, eax
    ret
ccn_yes:
    mov eax, 1
    ret
CtContainsN ENDP

CtFindAmbiguous PROC USES ebx esi edi, pCodon:DWORD
    LOCAL slot:DWORD
    mov slot, 64
cfa_find:
    mov eax, slot
    cmp eax, ctAmbNext
    jae cfa_add
    shl eax, 2
    lea edi, ctBases[eax]
    mov esi, pCodon
    mov al, [esi]
    cmp al, [edi]
    jne cfa_next
    mov al, [esi + 1]
    cmp al, [edi + 1]
    jne cfa_next
    mov al, [esi + 2]
    cmp al, [edi + 2]
    jne cfa_next
    mov eax, slot
    ret
cfa_next:
    inc slot
    jmp cfa_find
cfa_add:
    mov eax, ctAmbNext
    cmp eax, 125
    jae cfa_overflow
    mov slot, eax
    shl eax, 2
    lea edi, ctBases[eax]
    mov esi, pCodon
    mov al, [esi]
    mov [edi], al
    mov al, [esi + 1]
    mov [edi + 1], al
    mov al, [esi + 2]
    mov [edi + 2], al
    mov BYTE PTR [edi + 3], 0
    mov eax, slot
    shl eax, 1
    mov BYTE PTR ctLetter[eax], '?'
    mov BYTE PTR ctLetter[eax + 1], 0
    mov eax, slot
    shl eax, 5
    lea edi, ctName[eax]
    lea esi, ctAmbName
cfa_nm:
    mov al, [esi]
    mov [edi], al
    cmp al, 0
    je cfa_added
    inc esi
    inc edi
    jmp cfa_nm
cfa_added:
    inc ctAmbNext
    mov eax, slot
    ret
cfa_overflow:
    mov eax, 0FFFFFFFFh
    ret
CtFindAmbiguous ENDP

CtNoteSlot PROC USES eax edx, slot:DWORD
    mov eax, slot
    shl eax, 2
    inc DWORD PTR ctCount[eax]
    cmp DWORD PTR ctOrder[eax], 0
    jne cns_done
    inc ctNextOrder
    mov edx, ctNextOrder
    mov ctOrder[eax], edx
cns_done:
    ret
CtNoteSlot ENDP

TranslateCodons PROC USES ebx esi edi, pCtx:DWORD
    LOCAL hHeap:DWORD
    LOCAL hSeq:DWORD
    LOCAL hDetail:DWORD
    LOCAL hReport:DWORD
    LOCAL seqLen:DWORD
    LOCAL pos:DWORD
    LOCAL completeCount:DWORD
    LOCAL stopCount:DWORD
    LOCAL ambCount:DWORD
    LOCAL slot:DWORD
    LOCAL isAmb:DWORD
    LOCAL sortI:DWORD
    LOCAL sortJ:DWORD
    LOCAL sortMin:DWORD
    LOCAL firstPos:DWORD
    LOCAL leftCount:DWORD

    mov hSeq, 0
    mov hDetail, 0
    mov hReport, 0
    mov completeCount, 0
    mov stopCount, 0
    mov ambCount, 0
    mov ctNextOrder, 0
    mov ctAmbNext, 64

    mov ebx, pCtx
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).detailPath[0], 0
    jne tc_detail_ready
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke CopyZString, eax, ADDR ctDefDetail, MAX_PATH_LEN
tc_detail_ready:
    mov ebx, pCtx
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).seqOutPath[0], 0
    jne tc_seq_ready
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke CopyZString, eax, ADDR ctDefRna, MAX_PATH_LEN
tc_seq_ready:
    mov ebx, pCtx
    invoke ResolveCodonPath, ebx
    test eax, eax
    jz tc_missing
    mov ebx, pCtx
    invoke LoadCodonTable, ebx
    test eax, eax
    jnz tc_table_ok
    xor eax, eax
    ret

tc_missing:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_CODON_MISSING
    xor eax, eax
    ret

tc_table_ok:
    mov ebx, pCtx
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov seqLen, eax
    invoke GetProcessHeap
    mov hHeap, eax
    mov edx, seqLen
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz tc_mem
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).pOutBuf, eax

    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov edi, eax
    mov ecx, seqLen
tc_rna:
    cmp ecx, 0
    je tc_rna_done
    mov al, [esi]
    inc esi
    dec ecx
    cmp al, 'T'
    jne tc_store_rna
    mov al, 'U'
tc_store_rna:
    mov [edi], al
    inc edi
    jmp tc_rna
tc_rna_done:
    mov BYTE PTR [edi], 0

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).seqOutPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je tc_write
    mov hSeq, eax
    mov eax, hSeq
    mov ebx, pCtx
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    mov ecx, seqLen
    call WriteToFile
    mov eax, hSeq
    call CloseFile
    mov hSeq, 0

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).detailPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je tc_write
    mov hDetail, eax

    mov pos, 0
tc_codon_loop:
    mov eax, pos
    add eax, 3
    cmp eax, seqLen
    ja tc_codons_done

    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pOutBuf
    add esi, pos
    mov isAmb, 0
    invoke CtContainsN, esi
    test eax, eax
    jz tc_std
    invoke CtFindAmbiguous, esi
    cmp eax, 0FFFFFFFFh
    je tc_mem
    mov slot, eax
    mov isAmb, 1
    jmp tc_noted
tc_std:
    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pOutBuf
    add esi, pos
    mov al, [esi]
    call CtBaseValue
    mov edx, eax
    shl edx, 2
    mov al, [esi + 1]
    call CtBaseValue
    add edx, eax
    shl edx, 2
    mov al, [esi + 2]
    call CtBaseValue
    add edx, eax
    mov slot, edx

tc_noted:
    invoke CtNoteSlot, slot
    inc completeCount
    cmp isAmb, 1
    jne tc_check_stop
    inc ambCount
    jmp tc_write_ord
tc_check_stop:
    mov eax, slot
    shl eax, 1
    cmp BYTE PTR ctLetter[eax], '*'
    jne tc_write_ord
    inc stopCount

tc_write_ord:
    invoke WriteFileZStr, hDetail, ADDR ctOrd
    invoke WriteFileUInt32, hDetail, completeCount
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, pos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, slot
    shl eax, 2
    lea edx, ctBases[eax]
    invoke WriteFileZStr, hDetail, edx
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, slot
    shl eax, 1
    lea edx, ctLetter[eax]
    invoke WriteFileZStr, hDetail, edx
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, slot
    shl eax, 5
    lea edx, ctName[eax]
    invoke WriteFileZStr, hDetail, edx
    invoke WriteFileCrlf, hDetail

    add pos, 3
    jmp tc_codon_loop

tc_codons_done:
    mov eax, seqLen
    sub eax, pos
    cmp eax, 0
    je tc_no_trail
    invoke WriteFileZStr, hDetail, ADDR ctTrail
    mov ebx, pCtx
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    add edx, pos
    mov ecx, seqLen
    sub ecx, pos
    invoke WriteFileBytes, hDetail, edx, ecx
    invoke WriteFileCrlf, hDetail
tc_no_trail:

    mov ctSortCount, 0
    mov slot, 0
tc_collect:
    cmp slot, 125
    jae tc_collected
    mov eax, slot
    shl eax, 2
    cmp DWORD PTR ctOrder[eax], 0
    je tc_collect_next
    mov eax, ctSortCount
    shl eax, 2
    mov edx, slot
    mov ctSort[eax], edx
    inc ctSortCount
tc_collect_next:
    inc slot
    jmp tc_collect

tc_collected:
    mov sortI, 0
tc_sort_outer:
    mov eax, sortI
    cmp eax, ctSortCount
    jae tc_sort_done
    mov sortMin, eax
    mov eax, sortI
    inc eax
    mov sortJ, eax
tc_sort_inner:
    mov eax, sortJ
    cmp eax, ctSortCount
    jae tc_sort_swap
    mov eax, sortJ
    shl eax, 2
    mov edx, ctSort[eax]
    shl edx, 2
    mov ecx, ctOrder[edx]
    mov eax, sortMin
    shl eax, 2
    mov edx, ctSort[eax]
    shl edx, 2
    cmp ecx, ctOrder[edx]
    jae tc_sort_nextj
    mov eax, sortJ
    mov sortMin, eax
tc_sort_nextj:
    inc sortJ
    jmp tc_sort_inner
tc_sort_swap:
    mov eax, sortI
    cmp eax, sortMin
    je tc_sort_nexti
    mov eax, sortI
    shl eax, 2
    mov edx, ctSort[eax]
    mov ecx, sortMin
    shl ecx, 2
    mov ebx, ctSort[ecx]
    mov ctSort[eax], ebx
    mov ctSort[ecx], edx
tc_sort_nexti:
    inc sortI
    jmp tc_sort_outer

tc_sort_done:
    mov sortI, 0
tc_sum_loop:
    mov eax, sortI
    cmp eax, ctSortCount
    jae tc_sum_done
    mov eax, sortI
    shl eax, 2
    mov eax, ctSort[eax]
    mov slot, eax

    invoke WriteFileZStr, hDetail, ADDR ctSum
    mov eax, slot
    shl eax, 2
    lea edx, ctBases[eax]
    invoke WriteFileZStr, hDetail, edx
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, slot
    shl eax, 1
    lea edx, ctLetter[eax]
    invoke WriteFileZStr, hDetail, edx
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, slot
    shl eax, 5
    lea edx, ctName[eax]
    invoke WriteFileZStr, hDetail, edx
    invoke WriteFileZStr, hDetail, ADDR ctPipe
    mov eax, slot
    shl eax, 2
    mov edx, ctCount[eax]
    invoke WriteFileUInt32, hDetail, edx
    invoke WriteFileZStr, hDetail, ADDR ctPipe

    mov firstPos, 1
    mov pos, 0
tc_pos_loop:
    mov eax, pos
    add eax, 3
    cmp eax, seqLen
    ja tc_pos_done
    mov ebx, pCtx
    mov esi, (SESSION_CTX PTR [ebx]).pOutBuf
    add esi, pos
    mov eax, slot
    shl eax, 2
    lea edi, ctBases[eax]
    mov al, [esi]
    cmp al, [edi]
    jne tc_pos_next
    mov al, [esi + 1]
    cmp al, [edi + 1]
    jne tc_pos_next
    mov al, [esi + 2]
    cmp al, [edi + 2]
    jne tc_pos_next
    cmp firstPos, 1
    je tc_pos_write
    invoke WriteFileZStr, hDetail, ADDR ctSemi
tc_pos_write:
    mov firstPos, 0
    mov eax, pos
    inc eax
    invoke WriteFileUInt32, hDetail, eax
tc_pos_next:
    add pos, 3
    jmp tc_pos_loop
tc_pos_done:
    invoke WriteFileCrlf, hDetail
    inc sortI
    jmp tc_sum_loop

tc_sum_done:
    mov eax, hDetail
    call CloseFile
    mov hDetail, 0

    mov ebx, pCtx
    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je tc_write
    mov hReport, eax

    invoke WriteFileZStr, hReport, ADDR ctStatus
    invoke WriteFileUInt32, hReport, seqLen
    invoke WriteFileZStr, hReport, ADDR ctComplete
    invoke WriteFileUInt32, hReport, completeCount
    invoke WriteFileZStr, hReport, ADDR ctStop
    invoke WriteFileUInt32, hReport, stopCount
    invoke WriteFileZStr, hReport, ADDR ctAmb
    invoke WriteFileUInt32, hReport, ambCount
    invoke WriteFileZStr, hReport, ADDR ctLeft
    mov eax, seqLen
    sub eax, pos
    mov leftCount, eax
    invoke WriteFileUInt32, hReport, leftCount
    invoke WriteFileZStr, hReport, ADDR ctLeftSeq
    cmp leftCount, 0
    je tc_after_left
    mov ebx, pCtx
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    add edx, pos
    invoke WriteFileBytes, hReport, edx, leftCount
tc_after_left:
    invoke WriteFileZStr, hReport, ADDR ctRnaPath
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR ctDetailLbl
    mov ebx, pCtx
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke WriteFileZStr, hReport, eax
    invoke WriteFileZStr, hReport, ADDR ctEnd

    mov eax, hReport
    call CloseFile
    mov eax, 1
    ret

tc_mem:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    jmp tc_fail_close
tc_write:
    mov ebx, pCtx
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
tc_fail_close:
    cmp hDetail, 0
    je tc_fail_ret
    mov eax, hDetail
    call CloseFile
tc_fail_ret:
    xor eax, eax
    ret
TranslateCodons ENDP

END
