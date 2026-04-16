import json

# Manifiesto de comandos ejecutables por consola (modo efímero)
MANIFEST = {
    "commands": [
        {
            "command": "join",
            "description": "Unir todos los csv de este mes (auto-destrucción tras completar)",
            "script": "scrapping.Join"
        },
        {
            "command": "scrape",
            "description": "Ejecutar la minería diaria en España (auto-destrucción tras completar)",
            "script": "scrapping.Scrapping"
        }
    ]
}

if __name__ == "__main__":
    print(json.dumps(MANIFEST))
