INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
defaultBinPath      BYTE "compressed.dna", 0
hexDigits           BYTE "0123456789ABCDEF", 0
decodeBaseMap       BYTE "ACGT", 0

lblCompHeader       BYTE "STATUS=OK", 13, 10, "OPERATION=COMPRESS", 13, 10, "BIN_PATH=", 0
lblOrigLen          BYTE 13, 10, "ORIGINAL_LENGTH=", 0
lblOrigBytes        BYTE 13, 10, "ORIGINAL_BYTES=", 0
lblPart1Bytes       BYTE 13, 10, "PART1_BASE_BYTES=", 0
lblPart2Bytes       BYTE 13, 10, "PART2_NMASK_BYTES=", 0
lblHdrBytes         BYTE 13, 10, "HEADER_BYTES=", 0
lblTotalBinBytes    BYTE 13, 10, "TOTAL_BIN_BYTES=", 0
lblSavedPct         BYTE 13, 10, "SPACE_SAVED_PCT=", 0
lblPayloadSavedPct  BYTE 13, 10, "PAYLOAD_SAVED_PCT=", 0
lblChecksumHex      BYTE 13, 10, "CHECKSUM_HEX=", 0
lblRoundtrip        BYTE 13, 10, "ROUNDTRIP_VERIFIED=", 0
lblHexPreview       BYTE 13, 10, "HEX_PREVIEW=", 0
lblCompEnd          BYTE 13, 10, 0
strSpaceChar        BYTE " ", 0

.code

CompressTwoBit PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hHeap:DWORD
    LOCAL hFile:DWORD
    LOCAL seqLen:DWORD
    LOCAL part1Bytes:DWORD
    LOCAL part2Bytes:DWORD
    LOCAL totalBinBytes:DWORD
    LOCAL pPart1:DWORD
    LOCAL pPart2:DWORD
    LOCAL pVerify:DWORD
    LOCAL xorSum:DWORD
    LOCAL roundtripOk:DWORD
    LOCAL savedPct:DWORD
    LOCAL payloadSavedPct:DWORD
    LOCAL previewCount:DWORD
    LOCAL hexByteStr[4]:BYTE

    mov ebx, pCtx

    cmp BYTE PTR (SESSION_CTX PTR [ebx]).binPath[0], 0
    jne bin_path_ready
    lea eax, (SESSION_CTX PTR [ebx]).binPath
    invoke CopyZString, eax, ADDR defaultBinPath, MAX_PATH_LEN

bin_path_ready:
    mov eax, (SESSION_CTX PTR [ebx]).cleanLen
    mov seqLen, eax

    add eax, 3
    shr eax, 2
    mov part1Bytes, eax

    mov eax, seqLen
    add eax, 7
    shr eax, 3
    mov part2Bytes, eax

    mov eax, DNA2_HEADER_SIZE
    add eax, part1Bytes
    add eax, part2Bytes
    mov totalBinBytes, eax
    mov (SESSION_CTX PTR [ebx]).binLen, eax

    invoke GetProcessHeap
    mov hHeap, eax
    mov edx, totalBinBytes
    add edx, 16
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz comp_fail_mem
    mov (SESSION_CTX PTR [ebx]).pBinBuf, eax

    mov edi, eax
    mov DWORD PTR [edi], DNA2_MAGIC
    mov BYTE PTR [edi + 4], DNA2_VERSION
    mov eax, seqLen
    mov DWORD PTR [edi + 5], eax
    mov eax, part1Bytes
    mov DWORD PTR [edi + 9], eax
    mov eax, part2Bytes
    mov DWORD PTR [edi + 13], eax

    add edi, DNA2_HEADER_SIZE
    mov pPart1, edi
    add edi, part1Bytes
    mov pPart2, edi

    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov edi, pPart1
    mov ecx, seqLen
    xor edx, edx
    xor eax, eax

pack_part1_loop:
    cmp ecx, 0
    je pack_part1_tail
    mov al, [esi]
    inc esi
    dec ecx

    shl dl, 2
    cmp al, 'C'
    je code_c
    cmp al, 'G'
    je code_g
    cmp al, 'T'
    je code_t
    jmp code_advance

code_c:
    or dl, 1
    jmp code_advance

code_g:
    or dl, 2
    jmp code_advance

code_t:
    or dl, 3

code_advance:
    inc ah
    cmp ah, 4
    jne pack_part1_loop
    mov [edi], dl
    inc edi
    xor edx, edx
    xor ah, ah
    jmp pack_part1_loop

pack_part1_tail:
    cmp ah, 0
    je start_part2
    mov al, 4
    sub al, ah
    shl al, 1
    push ecx
    mov cl, al
    shl dl, cl
    pop ecx
    mov [edi], dl

start_part2:
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov edi, pPart2
    mov ecx, seqLen
    xor edx, edx
    xor eax, eax

pack_part2_loop:
    cmp ecx, 0
    je pack_part2_tail
    mov al, [esi]
    inc esi
    dec ecx

    shl dl, 1
    cmp al, 'N'
    jne mask_advance
    or dl, 1

mask_advance:
    inc ah
    cmp ah, 8
    jne pack_part2_loop
    mov [edi], dl
    inc edi
    xor edx, edx
    xor ah, ah
    jmp pack_part2_loop

pack_part2_tail:
    cmp ah, 0
    je compute_checksum
    mov al, 8
    sub al, ah
    push ecx
    mov cl, al
    shl dl, cl
    pop ecx
    mov [edi], dl

compute_checksum:
    mov esi, pPart1
    mov ecx, part1Bytes
    add ecx, part2Bytes
    xor eax, eax

xor_loop:
    cmp ecx, 0
    je store_checksum
    xor al, [esi]
    inc esi
    dec ecx
    jmp xor_loop

store_checksum:
    movzx eax, al
    mov xorSum, eax
    mov edi, (SESSION_CTX PTR [ebx]).pBinBuf
    mov BYTE PTR [edi + 17], al

    mov edx, seqLen
    add edx, 4
    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, edx
    test eax, eax
    jz comp_fail_mem
    mov pVerify, eax

    xor edx, edx
verify_decode_loop:
    cmp edx, seqLen
    je verify_compare

    mov eax, edx
    shr eax, 3
    mov esi, pPart2
    mov al, [esi + eax]
    mov ecx, edx
    and ecx, 7
    mov ah, 7
    sub ah, cl
    mov cl, ah
    shr al, cl
    and al, 1
    cmp al, 1
    je decoded_is_n

    mov eax, edx
    shr eax, 2
    mov esi, pPart1
    mov al, [esi + eax]
    mov ecx, edx
    and ecx, 3
    mov ah, 3
    sub ah, cl
    shl ah, 1
    mov cl, ah
    shr al, cl
    and eax, 3
    mov al, decodeBaseMap[eax]
    jmp store_decoded_char

decoded_is_n:
    mov al, 'N'

store_decoded_char:
    mov edi, pVerify
    mov [edi + edx], al
    inc edx
    jmp verify_decode_loop

verify_compare:
    mov esi, (SESSION_CTX PTR [ebx]).pCleanSeq
    mov edi, pVerify
    mov ecx, seqLen
    repe cmpsb
    jne verify_mismatch
    mov roundtripOk, 1
    jmp free_verify

verify_mismatch:
    mov roundtripOk, 0

free_verify:
    invoke HeapFree, hHeap, 0, pVerify

    mov eax, seqLen
    cmp eax, totalBinBytes
    jbe no_net_savings
    sub eax, totalBinBytes
    invoke CalcScaledPct, eax, seqLen
    mov savedPct, eax
    jmp calc_payload_savings

no_net_savings:
    mov savedPct, 0

calc_payload_savings:
    mov edx, part1Bytes
    add edx, part2Bytes
    mov eax, seqLen
    cmp eax, edx
    jbe no_payload_savings
    sub eax, edx
    invoke CalcScaledPct, eax, seqLen
    mov payloadSavedPct, eax
    jmp write_bin_file

no_payload_savings:
    mov payloadSavedPct, 0

write_bin_file:
    lea edx, (SESSION_CTX PTR [ebx]).binPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je comp_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pBinBuf
    mov ecx, totalBinBytes
    call WriteToFile

    mov eax, hFile
    call CloseFile

    invoke HeapAlloc, hHeap, HEAP_ZERO_FLAG, 4096
    test eax, eax
    jz comp_fail_mem
    mov (SESSION_CTX PTR [ebx]).pOutBuf, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblCompHeader
    mov edi, eax
    lea eax, (SESSION_CTX PTR [ebx]).binPath
    invoke WriteZStrCursor, edi, eax
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblOrigLen
    mov edi, eax
    invoke WriteUInt32Cursor, edi, seqLen
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblOrigBytes
    mov edi, eax
    invoke WriteUInt32Cursor, edi, seqLen
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPart1Bytes
    mov edi, eax
    invoke WriteUInt32Cursor, edi, part1Bytes
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPart2Bytes
    mov edi, eax
    invoke WriteUInt32Cursor, edi, part2Bytes
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblHdrBytes
    mov edi, eax
    invoke WriteUInt32Cursor, edi, DNA2_HEADER_SIZE
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblTotalBinBytes
    mov edi, eax
    invoke WriteUInt32Cursor, edi, totalBinBytes
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblSavedPct
    mov edi, eax
    invoke WriteScaledPctCursor, edi, savedPct
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblPayloadSavedPct
    mov edi, eax
    invoke WriteScaledPctCursor, edi, payloadSavedPct
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblChecksumHex
    mov edi, eax
    mov eax, xorSum
    mov edx, eax
    shr edx, 4
    and edx, 0Fh
    mov cl, hexDigits[edx]
    mov hexByteStr[0], cl
    mov edx, eax
    and edx, 0Fh
    mov cl, hexDigits[edx]
    mov hexByteStr[1], cl
    mov hexByteStr[2], 0
    invoke WriteZStrCursor, edi, ADDR hexByteStr
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblRoundtrip
    mov edi, eax
    invoke WriteUInt32Cursor, edi, roundtripOk
    mov edi, eax

    invoke WriteZStrCursor, edi, ADDR lblHexPreview
    mov edi, eax

    mov eax, totalBinBytes
    cmp eax, 32
    jbe set_preview_cnt
    mov eax, 32
set_preview_cnt:
    mov previewCount, eax
    mov esi, (SESSION_CTX PTR [ebx]).pBinBuf
    xor ecx, ecx

preview_loop:
    cmp ecx, previewCount
    je finish_comp_report
    cmp ecx, 0
    je format_hex_byte
    push ecx
    invoke WriteZStrCursor, edi, ADDR strSpaceChar
    mov edi, eax
    pop ecx

format_hex_byte:
    movzx eax, BYTE PTR [esi + ecx]
    mov edx, eax
    shr edx, 4
    and edx, 0Fh
    mov dl, hexDigits[edx]
    mov hexByteStr[0], dl
    mov edx, eax
    and edx, 0Fh
    mov dl, hexDigits[edx]
    mov hexByteStr[1], dl
    mov hexByteStr[2], 0
    push ecx
    invoke WriteZStrCursor, edi, ADDR hexByteStr
    mov edi, eax
    pop ecx
    inc ecx
    jmp preview_loop

finish_comp_report:
    invoke WriteZStrCursor, edi, ADDR lblCompEnd
    mov edi, eax

    sub edi, (SESSION_CTX PTR [ebx]).pOutBuf
    mov (SESSION_CTX PTR [ebx]).outLen, edi

    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je comp_fail_write
    mov hFile, eax

    mov eax, hFile
    mov edx, (SESSION_CTX PTR [ebx]).pOutBuf
    mov ecx, (SESSION_CTX PTR [ebx]).outLen
    call WriteToFile

    mov eax, hFile
    call CloseFile

    mov eax, 1
    ret

comp_fail_mem:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_BUFFER_LIMIT
    xor eax, eax
    ret

comp_fail_write:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_FILE_WRITE
    xor eax, eax
    ret
CompressTwoBit ENDP

END
