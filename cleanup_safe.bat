@echo off
echo ========================================
echo MotoMatch Safe Cleanup Script
echo ========================================
echo.
echo Eliminando solo archivos claramente innecesarios...
echo.

REM Solo archivos de backup obvios
echo Eliminando backups obvios...
del /q "app\algoritmo\utils.py.bak" 2>nul
del /q "app\templates\test.html.backup" 2>nul
del /q "app\static\js\test.js.backup" 2>nul
del /q "app\static\js\test.js.old" 2>nul

REM Solo archivos de salida de tests
echo Eliminando archivos de salida...
del /q "*_output.txt" 2>nul
del /q "*resultado*.txt" 2>nul
del /q "testneo.txt" 2>nul

REM Requirements duplicados (mantener requirements.txt)
echo Eliminando requirements duplicados...
del /q "requirements_updated.txt" 2>nul
del /q "requirements_production.txt" 2>nul
del /q "requirements_fix.txt" 2>nul
del /q "requirements_final.txt" 2>nul
del /q "requirements_compatible.txt" 2>nul

REM Archivos de diagnostico obvios
echo Eliminando diagnosticos...
del /q "diagnostico_*.py" 2>nul
del /q "debug_*.py" 2>nul

REM Scripts git
del /q "h -f origin main" 2>nul

REM Archivos con errores de sintaxis
del /q "simple_neo4j_test.py" 2>nul
del /q "test_moto_ideal_simple.py" 2>nul

echo.
echo Limpieza segura completada!
echo.
pause
