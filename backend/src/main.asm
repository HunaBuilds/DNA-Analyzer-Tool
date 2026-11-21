INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
flagOp              BYTE "-op", 0
flagIn              BYTE "-in", 0
flagOut             BYTE "-out", 0
flagBin             BYTE "-bin", 0
flagClean           BYTE "-clean", 0
flagSeqOut          BYTE "-seqout", 0
flagWin             BYTE "-win", 0
flagStep            BYTE "-step", 0
flagRaw             BYTE "-raw", 0
flagIn2             BYTE "-in2", 0
flagDetail          BYTE "-detail", 0
flagCodon           BYTE "-codon", 0
flagPattern         BYTE "-pattern", 0
flagLen             BYTE "-len", 0

opNameStats         BYTE "STATS", 0
opNameGcWin         BYTE "GC_WIN", 0
opNameCompress      BYTE "COMPRESS", 0
opNameRevComp       BYTE "REV_COMP", 0
opNameDnaToRna      BYTE "DNA_TO_RNA", 0
opNameTranslate     BYTE "TRANSLATE", 0
opNamePattern       BYTE "PATTERN", 0
opNameSimilarity    BYTE "SIMILARITY", 0
opNamePrimer        BYTE "PRIMER_TM", 0

tokenTruncated      DWORD 0

defaultOutPath      BYTE "dna_output.txt", 0
strDotChar          BYTE ".", 0
strZeroPad          BYTE "0", 0

strStatusErr        BYTE "STATUS=ERROR", 13, 10, "ERROR_CODE=", 0
strErrMsgLine       BYTE 13, 10, "ERROR_MSG=", 0
strErrPosLine       BYTE 13, 10, "ERROR_POS=", 0
strCrlf             BYTE 13, 10, 0

codeFileOpen        BYTE "ERR_FILE_OPEN", 0
codeEmptySeq        BYTE "ERR_EMPTY_SEQ", 0
codeNoHeader        BYTE "ERR_NO_HEADER", 0
codeInvalidChar     BYTE "ERR_INVALID_CHAR", 0
codeBufferLimit     BYTE "ERR_BUFFER_LIMIT", 0
codeInvalidParams   BYTE "ERR_INVALID_PARAMS", 0
codeAmbiguousN      BYTE "ERR_AMBIGUOUS_N", 0
codeFileWrite       BYTE "ERR_FILE_WRITE", 0
codeCodonMissing    BYTE "ERR_CODON_MISSING", 0
codeCodonInvalid    BYTE "ERR_CODON_INVALID", 0
codeEmptyPattern    BYTE "ERR_EMPTY_PATTERN", 0
codeInvalidPattern  BYTE "ERR_INVALID_PATTERN", 0
codeCompareUnavail  BYTE "ERR_COMPARE_UNAVAILABLE", 0
codeInvalidLength   BYTE "ERR_INVALID_LENGTH", 0
codePatternLength   BYTE "ERR_PATTERN_LENGTH", 0
codeSecondFile      BYTE "ERR_SECOND_FILE", 0
codeUnknown         BYTE "ERR_UNKNOWN", 0

msgFileOpen         BYTE "Unable to open input sequence file", 0
msgEmptySeq         BYTE "Input file contains no valid sequence nucleotides", 0
msgNoHeader         BYTE "Missing required FASTA header starting with >", 0
msgInvalidChar      BYTE "Unsupported character encountered in DNA sequence", 0
msgBufferLimit      BYTE "Heap memory allocation failed for sequence buffer", 0
msgInvalidParams    BYTE "Missing or invalid command-line arguments", 0
msgAmbiguousN       BYTE "Ambiguous base encountered in strict canonical mode", 0
msgFileWrite        BYTE "Unable to create or write output report file", 0
msgCodonMissing     BYTE "Codon table CSV file was not found", 0
msgCodonInvalid     BYTE "Codon table CSV is malformed or incomplete; expected 64 unique RNA codons and the required columns", 0
msgEmptyPattern     BYTE "Pattern is empty", 0
msgInvalidPattern   BYTE "Pattern must contain only A, T, G, C, or N", 0
msgCompareUnavail   BYTE "Comparison is unavailable because one or both sequences are empty", 0
msgInvalidLength    BYTE "Candidate length must be an integer from 1 through the sequence length", 0
msgPatternLength    BYTE "Pattern exceeds the maximum supported length", 0
msgSecondFile       BYTE "Unable to open the second FASTA file", 0
msgUnknown          BYTE "An unexpected processing error occurred", 0

.data?
ctx                 SESSION_CTX <>
tokenBuf            BYTE MAX_PATH_LEN DUP(?)
errReportBuf        BYTE DEFAULT_ERR_BUF_LEN DUP(?)
numScratchBuf       BYTE 16 DUP(?)

.code

ReadNextToken PROC USES esi edi, pCursor:DWORD, pOutToken:DWORD
    mov esi, pCursor
    mov edi, pOutToken

skip_ws:
    mov al, [esi]
    cmp al, 0
    je no_token
    cmp al, ASCII_SPACE
    je advance_ws
    cmp al, ASCII_TAB
    je advance_ws
    jmp start_token

advance_ws:
    inc esi
    jmp skip_ws

start_token:
    cmp al, ASCII_QUOTE
    je quoted_token

unquoted_loop:
    mov al, [esi]
    cmp al, 0
    je finish_token
    cmp al, ASCII_SPACE
    je finish_token
    cmp al, ASCII_TAB
    je finish_token
    mov [edi], al
    inc esi
    inc edi
    jmp unquoted_loop

quoted_token:
    inc esi
quoted_loop:
    mov al, [esi]
    cmp al, 0
    je finish_token
    cmp al, ASCII_QUOTE
    je end_quoted
    mov [edi], al
    inc esi
    inc edi
    jmp quoted_loop

end_quoted:
    inc esi

finish_token:
    mov BYTE PTR [edi], 0
    mov eax, esi
    ret

no_token:
    mov BYTE PTR [edi], 0
    xor eax, eax
    ret
ReadNextToken ENDP

ReadBoundedToken PROC USES esi edi ebx, pCursor:DWORD, pOut:DWORD, maxLen:DWORD
    mov tokenTruncated, 0
    mov esi, pCursor
    mov edi, pOut
    mov ebx, maxLen
    cmp ebx, 2
    jl rbt_none

rbt_skip:
    mov al, [esi]
    cmp al, 0
    je rbt_none
    cmp al, ASCII_SPACE
    je rbt_adv
    cmp al, ASCII_TAB
    je rbt_adv
    jmp rbt_start

rbt_adv:
    inc esi
    jmp rbt_skip

rbt_start:
    dec ebx
    cmp al, ASCII_QUOTE
    je rbt_quoted

rbt_unq:
    mov al, [esi]
    cmp al, 0
    je rbt_finish
    cmp al, ASCII_SPACE
    je rbt_finish
    cmp al, ASCII_TAB
    je rbt_finish
    cmp ebx, 0
    je rbt_ov_unq
    mov [edi], al
    inc esi
    inc edi
    dec ebx
    jmp rbt_unq

rbt_ov_unq:
    mov tokenTruncated, 1
rbt_drain_unq:
    mov al, [esi]
    cmp al, 0
    je rbt_finish
    cmp al, ASCII_SPACE
    je rbt_finish
    cmp al, ASCII_TAB
    je rbt_finish
    inc esi
    jmp rbt_drain_unq

rbt_quoted:
    inc esi
rbt_qloop:
    mov al, [esi]
    cmp al, 0
    je rbt_finish
    cmp al, ASCII_QUOTE
    je rbt_qend
    cmp ebx, 0
    je rbt_ov_q
    mov [edi], al
    inc esi
    inc edi
    dec ebx
    jmp rbt_qloop

rbt_ov_q:
    mov tokenTruncated, 1
rbt_drain_q:
    mov al, [esi]
    cmp al, 0
    je rbt_finish
    cmp al, ASCII_QUOTE
    je rbt_qend
    inc esi
    jmp rbt_drain_q

rbt_qend:
    inc esi

rbt_finish:
    mov BYTE PTR [edi], 0
    mov eax, esi
    ret

rbt_none:
    mov BYTE PTR [edi], 0
    xor eax, eax
    ret
ReadBoundedToken ENDP

CopyZString PROC USES esi edi ecx, pDest:DWORD, pSrc:DWORD, maxLen:DWORD
    mov edi, pDest
    mov esi, pSrc
    mov ecx, maxLen
    cmp ecx, 0
    jle copy_done
    dec ecx

copy_loop:
    cmp ecx, 0
    je copy_terminate
    mov al, [esi]
    cmp al, 0
    je copy_terminate
    mov [edi], al
    inc esi
    inc edi
    dec ecx
    jmp copy_loop

copy_terminate:
    mov BYTE PTR [edi], 0
copy_done:
    ret
CopyZString ENDP

AppendZString PROC USES esi edi, pDest:DWORD, pSrc:DWORD
    mov edi, pDest
    mov esi, pSrc

find_end:
    cmp BYTE PTR [edi], 0
    je append_loop
    inc edi
    jmp find_end

append_loop:
    mov al, [esi]
    mov [edi], al
    cmp al, 0
    je append_done
    inc esi
    inc edi
    jmp append_loop

append_done:
    ret
AppendZString ENDP

AppendUInt32 PROC USES ebx ecx edx edi, pDest:DWORD, value:DWORD
    mov eax, value
    lea edi, numScratchBuf
    add edi, 15
    mov BYTE PTR [edi], 0
    mov ebx, 10

convert_loop:
    xor edx, edx
    div ebx
    add dl, ASCII_ZERO
    dec edi
    mov [edi], dl
    test eax, eax
    jnz convert_loop

    invoke AppendZString, pDest, edi
    ret
AppendUInt32 ENDP

WriteZStrCursor PROC USES esi edi, pCursor:DWORD, pSrc:DWORD
    mov edi, pCursor
    mov esi, pSrc

wz_loop:
    mov al, [esi]
    cmp al, 0
    je wz_done
    mov [edi], al
    inc esi
    inc edi
    jmp wz_loop

wz_done:
    mov BYTE PTR [edi], 0
    mov eax, edi
    ret
WriteZStrCursor ENDP

WriteUInt32Cursor PROC USES ebx ecx edx edi, pCursor:DWORD, value:DWORD
    mov eax, value
    lea edi, numScratchBuf
    add edi, 15
    mov BYTE PTR [edi], 0
    mov ebx, 10

wc_loop:
    xor edx, edx
    div ebx
    add dl, ASCII_ZERO
    dec edi
    mov [edi], dl
    test eax, eax
    jnz wc_loop

    invoke WriteZStrCursor, pCursor, edi
    ret
WriteUInt32Cursor ENDP

CalcScaledPct PROC USES ebx edx, numVal:DWORD, denVal:DWORD
    mov ebx, denVal
    test ebx, ebx
    jz zero_pct
    mov eax, numVal
    mov edx, 10000
    mul edx
    div ebx
    ret

zero_pct:
    xor eax, eax
    ret
CalcScaledPct ENDP

WriteScaledPctCursor PROC USES ebx edx edi, pCursor:DWORD, scaledVal:DWORD
    mov edi, pCursor
    mov eax, scaledVal
    xor edx, edx
    mov ebx, 100
    div ebx
    push edx
    invoke WriteUInt32Cursor, edi, eax
    mov edi, eax
    invoke WriteZStrCursor, edi, ADDR strDotChar
    mov edi, eax
    pop edx
    cmp edx, 10
    jae write_frac
    push edx
    invoke WriteZStrCursor, edi, ADDR strZeroPad
    mov edi, eax
    pop edx

write_frac:
    invoke WriteUInt32Cursor, edi, edx
    ret
WriteScaledPctCursor ENDP

StrCompareI PROC USES esi edi, pStr1:DWORD, pStr2:DWORD
    mov esi, pStr1
    mov edi, pStr2

cmp_loop:
    mov al, [esi]
    mov ah, [edi]

    cmp al, 'a'
    jb check_ah
    cmp al, 'z'
    ja check_ah
    sub al, 20h

check_ah:
    cmp ah, 'a'
    jb do_cmp
    cmp ah, 'z'
    ja do_cmp
    sub ah, 20h

do_cmp:
    cmp al, ah
    jne not_equal
    cmp al, 0
    je is_equal
    inc esi
    inc edi
    jmp cmp_loop

is_equal:
    mov eax, 1
    ret

not_equal:
    xor eax, eax
    ret
StrCompareI ENDP

StrToUInt32 PROC USES ebx esi, pStr:DWORD
    mov esi, pStr
    xor eax, eax
    xor ebx, ebx

parse_digit:
    mov bl, [esi]
    cmp bl, 0
    je parse_done
    cmp bl, ASCII_ZERO
    jb parse_err
    cmp bl, ASCII_NINE
    ja parse_err
    sub bl, ASCII_ZERO
    imul eax, 10
    add eax, ebx
    inc esi
    jmp parse_digit

parse_done:
    ret

parse_err:
    xor eax, eax
    ret
StrToUInt32 ENDP

ParseCommandLine PROC USES ebx esi, pCtx:DWORD
    mov ebx, pCtx
    invoke GetCommandLineA
    mov esi, eax

    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax

cli_loop:
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz validate_cli
    mov esi, eax

    invoke StrCompareI, ADDR tokenBuf, ADDR flagRaw
    test eax, eax
    jz check_op_flag
    mov (SESSION_CTX PTR [ebx]).rawMode, 1
    jmp cli_loop

check_op_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagOp
    test eax, eax
    jz check_in_flag

    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax

    invoke StrCompareI, ADDR tokenBuf, ADDR opNameStats
    test eax, eax
    jz try_gc_win
    mov (SESSION_CTX PTR [ebx]).opCode, OP_STATS
    jmp cli_loop

try_gc_win:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNameGcWin
    test eax, eax
    jz try_compress
    mov (SESSION_CTX PTR [ebx]).opCode, OP_GC_WIN
    jmp cli_loop

try_compress:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNameCompress
    test eax, eax
    jz try_rev_comp
    mov (SESSION_CTX PTR [ebx]).opCode, OP_COMPRESS
    jmp cli_loop

try_rev_comp:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNameRevComp
    test eax, eax
    jz try_dna_rna
    mov (SESSION_CTX PTR [ebx]).opCode, OP_REV_COMP
    jmp cli_loop

try_dna_rna:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNameDnaToRna
    test eax, eax
    jz try_translate
    mov (SESSION_CTX PTR [ebx]).opCode, OP_DNA_TO_RNA
    jmp cli_loop

try_translate:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNameTranslate
    test eax, eax
    jz try_pattern
    mov (SESSION_CTX PTR [ebx]).opCode, OP_TRANSLATE
    jmp cli_loop

try_pattern:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNamePattern
    test eax, eax
    jz try_similarity
    mov (SESSION_CTX PTR [ebx]).opCode, OP_PATTERN
    jmp cli_loop

try_similarity:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNameSimilarity
    test eax, eax
    jz try_primer
    mov (SESSION_CTX PTR [ebx]).opCode, OP_SIMILARITY
    jmp cli_loop

try_primer:
    invoke StrCompareI, ADDR tokenBuf, ADDR opNamePrimer
    test eax, eax
    jz invalid_cli
    mov (SESSION_CTX PTR [ebx]).opCode, OP_PRIMER_TM
    jmp cli_loop

check_in_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagIn
    test eax, eax
    jz check_out_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).inPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_out_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagOut
    test eax, eax
    jz check_bin_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).outPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_bin_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagBin
    test eax, eax
    jz check_clean_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).binPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_clean_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagClean
    test eax, eax
    jz check_seqout_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).cleanPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_seqout_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagSeqOut
    test eax, eax
    jz check_win_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).seqOutPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_win_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagWin
    test eax, eax
    jz check_step_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    invoke StrToUInt32, ADDR tokenBuf
    mov (SESSION_CTX PTR [ebx]).winSize, eax
    jmp cli_loop

check_step_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagStep
    test eax, eax
    jz check_in2_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    invoke StrToUInt32, ADDR tokenBuf
    mov (SESSION_CTX PTR [ebx]).stepSize, eax
    jmp cli_loop

check_in2_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagIn2
    test eax, eax
    jz check_detail_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).inPath2
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_detail_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagDetail
    test eax, eax
    jz check_codon_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).detailPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_codon_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagCodon
    test eax, eax
    jz check_pattern_flag
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    lea eax, (SESSION_CTX PTR [ebx]).codonPath
    invoke CopyZString, eax, ADDR tokenBuf, MAX_PATH_LEN
    jmp cli_loop

check_pattern_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagPattern
    test eax, eax
    jz check_len_flag
    lea eax, (SESSION_CTX PTR [ebx]).patternBuf
    invoke ReadBoundedToken, esi, eax, PATTERN_MAX
    test eax, eax
    jz invalid_cli
    mov esi, eax
    cmp tokenTruncated, 0
    je cli_loop
    jmp pattern_too_long

check_len_flag:
    invoke StrCompareI, ADDR tokenBuf, ADDR flagLen
    test eax, eax
    jz cli_loop
    invoke ReadNextToken, esi, ADDR tokenBuf
    test eax, eax
    jz invalid_cli
    mov esi, eax
    invoke StrToUInt32, ADDR tokenBuf
    mov (SESSION_CTX PTR [ebx]).winSize, eax
    jmp cli_loop

validate_cli:
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).outPath[0], 0
    jne check_required
    lea eax, (SESSION_CTX PTR [ebx]).outPath
    invoke CopyZString, eax, ADDR defaultOutPath, MAX_PATH_LEN

check_required:
    cmp (SESSION_CTX PTR [ebx]).opCode, OP_NONE
    je invalid_cli
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).inPath[0], 0
    je invalid_cli
    mov eax, 1
    ret

invalid_cli:
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).outPath[0], 0
    jne set_param_err
    lea eax, (SESSION_CTX PTR [ebx]).outPath
    invoke CopyZString, eax, ADDR defaultOutPath, MAX_PATH_LEN

set_param_err:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_INVALID_PARAMS
    xor eax, eax
    ret

pattern_too_long:
    cmp BYTE PTR (SESSION_CTX PTR [ebx]).outPath[0], 0
    jne set_pat_len_err
    lea eax, (SESSION_CTX PTR [ebx]).outPath
    invoke CopyZString, eax, ADDR defaultOutPath, MAX_PATH_LEN
set_pat_len_err:
    mov (SESSION_CTX PTR [ebx]).errCode, ERR_PATTERN_LENGTH
    xor eax, eax
    ret
ParseCommandLine ENDP

WriteErrorReport PROC USES ebx ecx edx esi edi, pCtx:DWORD
    LOCAL hOut:DWORD
    mov ebx, pCtx
    mov BYTE PTR errReportBuf[0], 0

    invoke AppendZString, ADDR errReportBuf, ADDR strStatusErr

    mov eax, (SESSION_CTX PTR [ebx]).errCode
    cmp eax, ERR_FILE_OPEN
    je use_file_open
    cmp eax, ERR_EMPTY_SEQ
    je use_empty_seq
    cmp eax, ERR_NO_HEADER
    je use_no_header
    cmp eax, ERR_INVALID_CHAR
    je use_invalid_char
    cmp eax, ERR_BUFFER_LIMIT
    je use_buffer_limit
    cmp eax, ERR_INVALID_PARAMS
    je use_invalid_params
    cmp eax, ERR_AMBIGUOUS_N
    je use_ambiguous_n
    cmp eax, ERR_FILE_WRITE
    je use_file_write
    cmp eax, ERR_CODON_MISSING
    je use_codon_missing
    cmp eax, ERR_CODON_INVALID
    je use_codon_invalid
    cmp eax, ERR_EMPTY_PATTERN
    je use_empty_pattern
    cmp eax, ERR_INVALID_PATTERN
    je use_invalid_pattern
    cmp eax, ERR_COMPARE_UNAVAILABLE
    je use_compare_unavail
    cmp eax, ERR_INVALID_LENGTH
    je use_invalid_length
    cmp eax, ERR_PATTERN_LENGTH
    je use_pattern_length
    cmp eax, ERR_SECOND_FILE
    je use_second_file

    lea esi, codeUnknown
    lea edi, msgUnknown
    jmp build_err_body

use_file_open:
    lea esi, codeFileOpen
    lea edi, msgFileOpen
    jmp build_err_body

use_empty_seq:
    lea esi, codeEmptySeq
    lea edi, msgEmptySeq
    jmp build_err_body

use_no_header:
    lea esi, codeNoHeader
    lea edi, msgNoHeader
    jmp build_err_body

use_invalid_char:
    lea esi, codeInvalidChar
    lea edi, msgInvalidChar
    jmp build_err_body

use_buffer_limit:
    lea esi, codeBufferLimit
    lea edi, msgBufferLimit
    jmp build_err_body

use_invalid_params:
    lea esi, codeInvalidParams
    lea edi, msgInvalidParams
    jmp build_err_body

use_ambiguous_n:
    lea esi, codeAmbiguousN
    lea edi, msgAmbiguousN
    jmp build_err_body

use_file_write:
    lea esi, codeFileWrite
    lea edi, msgFileWrite
    jmp build_err_body

use_codon_missing:
    lea esi, codeCodonMissing
    lea edi, msgCodonMissing
    jmp build_err_body

use_codon_invalid:
    lea esi, codeCodonInvalid
    lea edi, msgCodonInvalid
    jmp build_err_body

use_empty_pattern:
    lea esi, codeEmptyPattern
    lea edi, msgEmptyPattern
    jmp build_err_body

use_invalid_pattern:
    lea esi, codeInvalidPattern
    lea edi, msgInvalidPattern
    jmp build_err_body

use_compare_unavail:
    lea esi, codeCompareUnavail
    lea edi, msgCompareUnavail
    jmp build_err_body

use_invalid_length:
    lea esi, codeInvalidLength
    lea edi, msgInvalidLength
    jmp build_err_body

use_pattern_length:
    lea esi, codePatternLength
    lea edi, msgPatternLength
    jmp build_err_body

use_second_file:
    lea esi, codeSecondFile
    lea edi, msgSecondFile

build_err_body:
    invoke AppendZString, ADDR errReportBuf, esi
    invoke AppendZString, ADDR errReportBuf, ADDR strErrMsgLine
    invoke AppendZString, ADDR errReportBuf, edi
    invoke AppendZString, ADDR errReportBuf, ADDR strErrPosLine
    invoke AppendUInt32, ADDR errReportBuf, (SESSION_CTX PTR [ebx]).errPos
    invoke AppendZString, ADDR errReportBuf, ADDR strCrlf

    lea edx, (SESSION_CTX PTR [ebx]).outPath
    call CreateOutputFile
    cmp eax, INVALID_HANDLE_VALUE
    je report_done
    mov hOut, eax

    lea edi, errReportBuf
    xor ecx, ecx
count_report_len:
    cmp BYTE PTR [edi], 0
    je write_report_bytes
    inc edi
    inc ecx
    jmp count_report_len

write_report_bytes:
    mov eax, hOut
    lea edx, errReportBuf
    call WriteToFile
    mov eax, hOut
    call CloseFile

report_done:
    ret
WriteErrorReport ENDP

CleanupSession PROC USES ebx, pCtx:DWORD
    LOCAL hHeap:DWORD
    mov ebx, pCtx
    invoke GetProcessHeap
    mov hHeap, eax

    mov eax, (SESSION_CTX PTR [ebx]).pRawBuf
    test eax, eax
    jz free_clean
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pRawBuf, 0

free_clean:
    mov eax, (SESSION_CTX PTR [ebx]).pCleanSeq
    test eax, eax
    jz free_header
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pCleanSeq, 0

free_header:
    mov eax, (SESSION_CTX PTR [ebx]).pHeaderBuf
    test eax, eax
    jz free_out
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pHeaderBuf, 0

free_out:
    mov eax, (SESSION_CTX PTR [ebx]).pOutBuf
    test eax, eax
    jz free_bin
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pOutBuf, 0

free_bin:
    mov eax, (SESSION_CTX PTR [ebx]).pBinBuf
    test eax, eax
    jz free_seq2
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pBinBuf, 0

free_seq2:
    mov eax, (SESSION_CTX PTR [ebx]).pCleanSeq2
    test eax, eax
    jz free_hdr2
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pCleanSeq2, 0

free_hdr2:
    mov eax, (SESSION_CTX PTR [ebx]).pHeaderBuf2
    test eax, eax
    jz cleanup_done
    invoke HeapFree, hHeap, 0, eax
    mov (SESSION_CTX PTR [ebx]).pHeaderBuf2, 0

cleanup_done:
    ret
CleanupSession ENDP

main PROC
    lea edi, ctx
    mov ecx, SIZEOF SESSION_CTX
    xor al, al
    rep stosb

    invoke ParseCommandLine, ADDR ctx
    test eax, eax
    jz fatal_exit

    cmp ctx.rawMode, 1
    je load_cached_seq

    invoke LoadAndParseFasta, ADDR ctx
    test eax, eax
    jz fatal_exit
    jmp dispatch_op

load_cached_seq:
    invoke LoadRawSequence, ADDR ctx
    test eax, eax
    jz fatal_exit

dispatch_op:
    mov eax, ctx.opCode
    cmp eax, OP_STATS
    je run_stats
    cmp eax, OP_GC_WIN
    je run_gc_win
    cmp eax, OP_COMPRESS
    je run_compress
    cmp eax, OP_REV_COMP
    je run_rev_comp
    cmp eax, OP_DNA_TO_RNA
    je run_dna_rna
    cmp eax, OP_TRANSLATE
    je run_translate
    cmp eax, OP_PATTERN
    je run_pattern
    cmp eax, OP_SIMILARITY
    je run_similarity
    cmp eax, OP_PRIMER_TM
    je run_primer
    mov ctx.errCode, ERR_INVALID_PARAMS
    jmp fatal_exit

run_stats:
    invoke ComputeDnaStats, ADDR ctx
    jmp check_op_status

run_gc_win:
    invoke RunGcWindow, ADDR ctx
    jmp check_op_status

run_compress:
    invoke CompressTwoBit, ADDR ctx
    jmp check_op_status

run_rev_comp:
    invoke ComputeReverseComplement, ADDR ctx
    jmp check_op_status

run_dna_rna:
    invoke ConvertDnaToRna, ADDR ctx
    jmp check_op_status

run_translate:
    invoke TranslateCodons, ADDR ctx
    jmp check_op_status

run_pattern:
    invoke SearchDnaPattern, ADDR ctx
    jmp check_op_status

run_similarity:
    invoke CompareSequences, ADDR ctx
    jmp check_op_status

run_primer:
    invoke ScanPrimerTm, ADDR ctx

check_op_status:
    test eax, eax
    jz fatal_exit

    invoke CleanupSession, ADDR ctx
    invoke ExitProcess, 0

fatal_exit:
    invoke WriteErrorReport, ADDR ctx
    invoke CleanupSession, ADDR ctx
    invoke ExitProcess, 1
main ENDP

END main
