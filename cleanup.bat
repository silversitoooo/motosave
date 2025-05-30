@echo off
echo ========================================
echo MotoMatch Project Cleanup Script
echo ========================================
echo.
echo Eliminando archivos innecesarios...
echo.

REM Archivos de backup
echo Eliminando archivos de backup...
del /q "app\algoritmo\utils.py.bak" 2>nul
del /q "app\templates\test.html.backup" 2>nul
del /q "app\static\js\test.js.backup" 2>nul
del /q "app\static\js\test.js.old" 2>nul
del /q "app\__init__.py.fixed" 2>nul

REM Archivos de diagnostico
echo Eliminando archivos de diagnostico...
del /q "diagnostico_*.py" 2>nul
del /q "debug_*.py" 2>nul

REM Archivos de salida/resultados
echo Eliminando archivos de salida...
del /q "*_output.txt" 2>nul
del /q "*resultado*.txt" 2>nul
del /q "prueba_*.txt" 2>nul
del /q "demo_output.txt" 2>nul
del /q "testneo.txt" 2>nul

REM Requirements duplicados (mantener solo requirements.txt)
echo Eliminando requirements duplicados...
del /q "requirements_updated.txt" 2>nul
del /q "requirements_production.txt" 2>nul
del /q "requirements_fix.txt" 2>nul
del /q "requirements_final.txt" 2>nul
del /q "requirements_compatible.txt" 2>nul

REM Scripts de PowerShell
echo Eliminando scripts PS...
del /q "*.ps1" 2>nul
del /q "h -f origin main" 2>nul

REM Archivos con errores de sintaxis
echo Eliminando archivos rotos...
del /q "simple_neo4j_test.py" 2>nul
del /q "test_moto_ideal_simple.py" 2>nul

REM Archivos HTML de prueba
echo Eliminando HTML de prueba...
del /q "simple_recommender.html" 2>nul
del /q "test_bubbles.html" 2>nul

REM Archivos de evaluacion/prueba
echo Eliminando archivos de evaluacion...
del /q "evaluacion_*.py" 2>nul
del /q "prueba_*.py" 2>nul
del /q "check_*.py" 2>nul
del /q "diagnose_*.py" 2>nul
del /q "verify_*.py" 2>nul
del /q "fix_*.py" 2>nul

REM Archivos de test duplicados/viejos
echo Eliminando tests duplicados...
del /q "test_adapter_correct.py" 2>nul
del /q "test_debug_moto_ideal.py" 2>nul
del /q "test_dual_input_compatibility.py" 2>nul
del /q "test_ideal_moto.py" 2>nul
del /q "test_integracion_completa.py" 2>nul
del /q "test_label_propagation_fixed.py" 2>nul
del /q "test_label_propagation.py" 2>nul
del /q "test_log.py" 2>nul
del /q "test_moto_detail_url.py" 2>nul
del /q "test_moto_ideal_complete.py" 2>nul
del /q "test_neo4j.py" 2>nul
del /q "test_projeto_principal.py" 2>nul
del /q "test_qualitative_integration.py" 2>nul
del /q "test_range_inputs.py" 2>nul
del /q "test_reasons_serialization.py" 2>nul
del /q "test_recomendaciones_completas.py" 2>nul
del /q "test_recomendador_corregido.py" 2>nul
del /q "test_simple_compatibility.py" 2>nul
del /q "test_simple.py" 2>nul
del /q "test_templates.py" 2>nul
del /q "test_corregido.py" 2>nul

REM Archivos de run duplicados
echo Eliminando archivos run duplicados...
del /q "run_application.py" 2>nul
del /q "run_app_fixed.py" 2>nul
del /q "run_clean.py" 2>nul
del /q "run_debug.py" 2>nul
del /q "run_demo_standalone.py" 2>nul
del /q "run_fixed.py" 2>nul
del /q "run_fixed_app_corrected.py" 2>nul
del /q "run_fixed_app_final.py" 2>nul
del /q "run_integrado.py" 2>nul
del /q "run_minimal_test.py" 2>nul
del /q "run_production.py" 2>nul
del /q "run_simple.py" 2>nul

REM Archivos de adaptador duplicados/viejos
echo Eliminando adaptadores duplicados...
del /q "moto_adapter.py" 2>nul
del /q "moto_adapter_correct.py" 2>nul
del /q "moto_adapter_fixed.py" 2>nul

REM Archivos de algoritmo duplicados
echo Eliminando algoritmos duplicados...
del /q "algoritmo_standalone.py" 2>nul
del /q "simple_fix.py" 2>nul

REM Archivos varios
echo Eliminando archivos varios...
del /q "comprehensive_database_fix.py" 2>nul
del /q "initialize_db.py" 2>nul
del /q "load_neo4j_data.py" 2>nul
del /q "unify_credentials.py" 2>nul
del /q "update_routes.py" 2>nul
del /q "auth_redirects.py" 2>nul
del /q "auth_routes.py" 2>nul
del /q "redirects.py" 2>nul
del /q "recomendaciones.py" 2>nul
del /q "simple_recommender_safe.py" 2>nul

echo.
echo ========================================
echo Limpieza completada!
echo ========================================
echo.
echo Archivos eliminados:
echo - Backups (.bak, .backup, .old)
echo - Diagnosticos y debug
echo - Archivos de salida (.txt)
echo - Requirements duplicados
echo - Scripts PowerShell
echo - Tests duplicados/rotos
echo - Archivos run duplicados
echo - Adaptadores duplicados
echo.
pause
