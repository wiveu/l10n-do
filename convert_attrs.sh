#!/bin/bash

# Script para convertir attrs a la nueva sintaxis de Odoo 18

# Función para convertir attrs simples
convert_attrs() {
    local file="$1"
    
    # Convertir attrs invisibles simples
    sed -i '' "s/attrs=\"{'invisible':\[([^]]*)\]}\"/invisible=\"\1\"/g" "$file"
    
    # Convertir attrs readonly simples  
    sed -i '' "s/attrs=\"{'readonly':\[([^]]*)\]}\"/readonly=\"\1\"/g" "$file"
    
    # Convertir attrs required simples
    sed -i '' "s/attrs=\"{'required':\[([^]]*)\]}\"/required=\"\1\"/g" "$file"
    
    # Limpiar algunos patrones comunes
    sed -i '' "s/\('state', '=', 'draft'\)/state == 'draft'/g" "$file"
    sed -i '' "s/\('state', '!=', 'draft'\)/state != 'draft'/g" "$file"
    sed -i '' "s/\('state', '=', 'cancel'\)/state == 'cancel'/g" "$file" 
    sed -i '' "s/\('state', '!=', 'cancel'\)/state != 'cancel'/g" "$file"
    sed -i '' "s/\('state', '=', 'posted'\)/state == 'posted'/g" "$file"
    sed -i '' "s/\('state', '!=', 'posted'\)/state != 'posted'/g" "$file"
}

# Aplicar conversiones a archivos específicos
for file in $(find /Users/raulovalle/odoo/odoo18/custom/jenrax/l10n-do -name "*.xml" -exec grep -l "attrs=" {} \;); do
    echo "Procesando: $file"
    convert_attrs "$file"
done
