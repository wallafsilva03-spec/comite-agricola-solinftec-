"""Converte a planilha 'linha_do_tempo_comite.xlsx' (uma linha por evento) para um
CSV pronto para importar na tabela `linha_do_tempo` do Supabase.

Uso:
    pip install openpyxl
    python scripts/convert_linha_do_tempo.py caminho/para/linha_do_tempo.xlsx [saida.csv]

Faz duas conversões que o Excel exporta em formato incompatível com o Postgres:
- Data: de "DD/MM/AAAA" para "AAAA-MM-DD" (coluna `data`, tipo date).
- Números: de "12719,25" (vírgula decimal) para "12719.25" (ponto decimal).
"""

import csv
import datetime
import re
import sys

import openpyxl

OUT_COLUMNS = [
    'regional', 'unidade', 'frente', 'codigo_equipamento', 'equipamento',
    'codigo_operador', 'operador', 'data', 'hora_inicial', 'hora_final',
    'codigo_operacao', 'atividade', 'classificacao', 'codigo_fazenda',
    'codigo_zona', 'codigo_talhao', 'fazenda', 'horimetro_inicial',
    'horimetro_final', 'horimetro_secundario', 'velocidade_media',
]

DATE_RE = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4})$')


def conv_data(value):
    if value is None:
        return ''
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d')
    text = str(value).strip()
    match = DATE_RE.match(text)
    if match:
        day, month, year = match.groups()
        return f'{year}-{int(month):02d}-{int(day):02d}'
    return text


def conv_hora(value):
    if value is None:
        return ''
    if isinstance(value, datetime.time):
        return value.strftime('%H:%M:%S')
    return str(value).strip()


def conv_num(value):
    if value is None:
        return ''
    text = str(value).strip()
    if not text:
        return ''
    return text.replace('.', '').replace(',', '.') if ',' in text else text


def convert(input_path, output_path):
    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    next(rows)  # descarta o cabeçalho original

    written, skipped = 0, 0
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(OUT_COLUMNS)
        for row in rows:
            (regional, unidade, frente, cod_equip, equip, cod_op, nome, data_h,
             hora_ini, hora_fim, cod_operacao, atividade, classificacao,
             cod_fazenda, cod_zona, cod_talhao, fazenda, hor_ini, hor_fim,
             hor_sec, vel_media) = row

            data = conv_data(data_h)
            h_ini = conv_hora(hora_ini)
            h_fim = conv_hora(hora_fim)
            if not data or not h_ini or not h_fim or not atividade or not classificacao:
                skipped += 1
                continue

            writer.writerow([
                regional, unidade, frente, cod_equip, equip, cod_op, nome, data,
                h_ini, h_fim, cod_operacao, atividade, classificacao, cod_fazenda,
                cod_zona, cod_talhao, fazenda, conv_num(hor_ini), conv_num(hor_fim),
                conv_num(hor_sec), conv_num(vel_media),
            ])
            written += 1

    print(f'Linhas convertidas: {written} | ignoradas (dados incompletos): {skipped}')
    print(f'Arquivo gerado: {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python scripts/convert_linha_do_tempo.py entrada.xlsx [saida.csv]')
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'linha_do_tempo_import.csv'
    convert(input_path, output_path)
