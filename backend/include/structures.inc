SESSION_CTX STRUCT
    opCode          DWORD ?
    rawMode         DWORD ?
    winSize         DWORD ?
    stepSize        DWORD ?
    pRawBuf         DWORD ?
    rawBytes        DWORD ?
    pCleanSeq       DWORD ?
    cleanLen        DWORD ?
    pHeaderBuf      DWORD ?
    headerLen       DWORD ?
    pOutBuf         DWORD ?
    outLen          DWORD ?
    pBinBuf         DWORD ?
    binLen          DWORD ?
    errCode         DWORD ?
    errPos          DWORD ?
    inPath          BYTE MAX_PATH_LEN DUP(?)
    outPath         BYTE MAX_PATH_LEN DUP(?)
    binPath         BYTE MAX_PATH_LEN DUP(?)
    cleanPath       BYTE MAX_PATH_LEN DUP(?)
    seqOutPath      BYTE MAX_PATH_LEN DUP(?)
    pCleanSeq2      DWORD ?
    cleanLen2       DWORD ?
    pHeaderBuf2     DWORD ?
    headerLen2      DWORD ?
    inPath2         BYTE MAX_PATH_LEN DUP(?)
    detailPath      BYTE MAX_PATH_LEN DUP(?)
    codonPath       BYTE MAX_PATH_LEN DUP(?)
    patternBuf      BYTE PATTERN_MAX DUP(?)
SESSION_CTX ENDS

STATS_RESULT STRUCT
    totalLen        DWORD ?
    validCanonical  DWORD ?
    countA          DWORD ?
    countT          DWORD ?
    countG          DWORD ?
    countC          DWORD ?
    countN          DWORD ?
    pctA            DWORD ?
    pctT            DWORD ?
    pctG            DWORD ?
    pctC            DWORD ?
    pctGC           DWORD ?
    pctAT           DWORD ?
STATS_RESULT ENDS
