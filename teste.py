from ideb_mcp.server import REGISTROS, ideb_lookup, ideb_buscar, ideb_ranking, ideb_comparar, ideb_estatisticas

print("=== TESTE DO SERVIDOR IDEB MCP ===\n")

print("📊 Total de municípios carregados:", len(REGISTROS))
print()

print("🔍 Teste 1: Buscar municípios em RO")
print(ideb_buscar(estado="RO", limite=3))
print()

print("🔍 Teste 2: Lookup de Ariquemes (RO)")
print(ideb_lookup(municipio="Ariquemes", estado="RO"))
print()

print("🏆 Teste 3: Ranking RO em 2023")
print(ideb_ranking("RO", ano="2023", limite=5))
print()

print("⚖️ Teste 4: Comparar municípios")
print(ideb_comparar(["Ariquemes", "Cabixi"], estado="RO", ano="2023"))
print()

print("📈 Teste 5: Estatísticas RO 2023")
print(ideb_estatisticas(estado="RO", ano="2023"))
print()

print("✅ Todos os testes executados!")