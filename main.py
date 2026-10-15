import argparse

def ejecutar_benchmarks():
    from bench.ordenamientos import main as bench_ordenamientos
    from bench.cache import main as bench_cache
    print("------Bench de Ordenamientos------")
    bench_ordenamientos()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Cache------")
    bench_cache()

def main():
    parser = argparse.ArgumentParser(description="Cripta Dungeon")
    parser.add_argument("--bench", action="store_true", help="ejecuta los benchmarks en lugar del juego")
    args = parser.parse_args()

    if args.bench:
        ejecutar_benchmarks()
        return
    print("Iniciando cripta dungeon...")

if __name__ == "__main__":
    main()