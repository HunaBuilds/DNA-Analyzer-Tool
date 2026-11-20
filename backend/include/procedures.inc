ParseCommandLine            PROTO, pCtx:DWORD
WriteErrorReport            PROTO, pCtx:DWORD
CleanupSession              PROTO, pCtx:DWORD
CopyZString                 PROTO, pDest:DWORD, pSrc:DWORD, maxLen:DWORD
AppendZString               PROTO, pDest:DWORD, pSrc:DWORD
AppendUInt32                PROTO, pDest:DWORD, value:DWORD
WriteZStrCursor             PROTO, pCursor:DWORD, pSrc:DWORD
WriteUInt32Cursor           PROTO, pCursor:DWORD, value:DWORD
WriteScaledPctCursor        PROTO, pCursor:DWORD, scaledVal:DWORD
CalcScaledPct               PROTO, numVal:DWORD, denVal:DWORD
StrCompareI                 PROTO, pStr1:DWORD, pStr2:DWORD
StrToUInt32                 PROTO, pStr:DWORD

LoadAndParseFasta           PROTO, pCtx:DWORD
LoadRawSequence             PROTO, pCtx:DWORD

ComputeDnaStats             PROTO, pCtx:DWORD
RunGcWindow                 PROTO, pCtx:DWORD
CompressTwoBit              PROTO, pCtx:DWORD
ComputeReverseComplement    PROTO, pCtx:DWORD
ConvertDnaToRna             PROTO, pCtx:DWORD
