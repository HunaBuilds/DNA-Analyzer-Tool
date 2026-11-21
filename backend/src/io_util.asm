INCLUDE Irvine32.inc
INCLUDE constants.inc
INCLUDE structures.inc
INCLUDE procedures.inc

.data
ioCrlf              BYTE 13, 10, 0
ioDot               BYTE ".", 0
ioZeroChar          BYTE "0", 0
ioDigits            BYTE 16 DUP(0)

.code

WriteFileBytes PROC hFile:DWORD, pBuf:DWORD, nBytes:DWORD
    cmp nBytes, 0
    je wfb_done
    mov eax, hFile
    mov edx, pBuf
    mov ecx, nBytes
    call WriteToFile
wfb_done:
    ret
WriteFileBytes ENDP

WriteFileZStr PROC USES esi ecx, hFile:DWORD, pStr:DWORD
    mov esi, pStr
    xor ecx, ecx
wfz_count:
    cmp BYTE PTR [esi + ecx], 0
    je wfz_go
    inc ecx
    jmp wfz_count
wfz_go:
    invoke WriteFileBytes, hFile, pStr, ecx
    ret
WriteFileZStr ENDP

WriteFileCrlf PROC, hFile:DWORD
    invoke WriteFileZStr, hFile, ADDR ioCrlf
    ret
WriteFileCrlf ENDP

WriteFileUInt32 PROC USES eax ebx edx edi, hFile:DWORD, value:DWORD
    mov eax, value
    lea edi, ioDigits
    add edi, 15
    mov BYTE PTR [edi], 0
    mov ebx, 10
wfu_loop:
    xor edx, edx
    div ebx
    add dl, ASCII_ZERO
    dec edi
    mov [edi], dl
    test eax, eax
    jnz wfu_loop
    invoke WriteFileZStr, hFile, edi
    ret
WriteFileUInt32 ENDP

WriteFileScaledPct PROC USES eax ebx edx, hFile:DWORD, scaledVal:DWORD
    LOCAL frac:DWORD
    mov eax, scaledVal
    xor edx, edx
    mov ebx, 100
    div ebx
    mov frac, edx
    invoke WriteFileUInt32, hFile, eax
    invoke WriteFileZStr, hFile, ADDR ioDot
    mov eax, frac
    cmp eax, 10
    jae wfs_frac
    invoke WriteFileZStr, hFile, ADDR ioZeroChar
wfs_frac:
    invoke WriteFileUInt32, hFile, frac
    ret
WriteFileScaledPct ENDP

END
