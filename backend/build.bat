@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist "C:\Irvine" (
    set "INCLUDE=C:\Irvine;%INCLUDE%"
    set "LIB=C:\Irvine;%LIB%"
)
where ml >nul 2>&1
if errorlevel 1 call :setup_ml
where ml >nul 2>&1
if errorlevel 1 (
    echo MASM ml.exe was not found. Install the x86 Visual C++ build tools or run from a developer prompt.
    exit /b 1
)
if not exist build mkdir build
ml /c /coff /I include /Fo build\main.obj src\main.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\fasta.obj src\fasta.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\statistics.obj src\statistics.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\gc_window.obj src\gc_window.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\compression.obj src\compression.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\reverse_complement.obj src\reverse_complement.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\dna_to_rna.obj src\dna_to_rna.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\io_util.obj src\io_util.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\codon_translate.obj src\codon_translate.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\pattern_search.obj src\pattern_search.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\similarity.obj src\similarity.asm
if errorlevel 1 exit /b 1
ml /c /coff /I include /Fo build\primer_tm.obj src\primer_tm.asm
if errorlevel 1 exit /b 1
link /subsystem:console /out:build\DNAAnalyzer.exe build\main.obj build\fasta.obj build\statistics.obj build\gc_window.obj build\compression.obj build\reverse_complement.obj build\dna_to_rna.obj build\io_util.obj build\codon_translate.obj build\pattern_search.obj build\similarity.obj build\primer_tm.obj Irvine32.lib kernel32.lib user32.lib
if errorlevel 1 exit /b 1
echo Build succeeded: build\DNAAnalyzer.exe
exit /b 0

:setup_ml
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" exit /b 0
set "MLFILE="
for /f "usebackq delims=" %%M in (`"%VSWHERE%" -latest -products * -find VC\Tools\MSVC\*\bin\Hostx86\x86\ml.exe`) do set "MLFILE=%%M"
if not defined MLFILE exit /b 0
for %%D in ("%MLFILE%") do set "PATH=%%~dpD;%PATH%"
exit /b 0
