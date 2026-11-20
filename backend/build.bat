@echo off
setlocal
if exist "C:\Irvine" (
    set "INCLUDE=C:\Irvine;%INCLUDE%"
    set "LIB=C:\Irvine;%LIB%"
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
link /subsystem:console /out:build\DNAAnalyzer.exe build\main.obj build\fasta.obj build\statistics.obj build\gc_window.obj build\compression.obj build\reverse_complement.obj build\dna_to_rna.obj Irvine32.lib kernel32.lib user32.lib
if errorlevel 1 exit /b 1
echo Build succeeded: build\DNAAnalyzer.exe
