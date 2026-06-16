"""Importa a planilha 'linha_do_tempo_comite.xlsx' (uma linha por evento) direto para a
tabela `linha_do_tempo` do Supabase via API REST, sem precisar do importador de CSV
da interface (que vinha dando erro de cabeçalho incompatível).

Uso:
    pip install openpyxl requests
    export SUPABASE_URL="https://xxxxxxxxxxxxx.supabase.co"
    export SUPABASE_SERVICE_KEY="sua-service-role-key"   # NÃO é a anon key
    python scripts/import_to_supabase.py caminho/para/planilha.xlsx

A service_role key fica em Project Settings > API > "service_role" (secret).
Use-a só localmente, nunca cole no HTML do painel nem em código publicado.

Pode rodar de novo com planilhas diferentes para ir empilhando dados na mesma tabela.
"""

import datetime
import os
import re
import sys

import openpyxl
import requests

TABLE_NAME = 'linha_do_tempo'
BATCH_SIZE = 500

DATE_RE = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4})$')


def conv_data(value):
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d')
    text = str(value).strip()
    match = DATE_RE.match(text)
    if match:
        day, month, year = match.groups()
        return f'{year}-{int(month):02d}-{int(day):02d}'
    return text or None


def conv_hora(value):
    if value is None:
        return None
    if isinstance(value, datetime.time):
        return value.strftime('%H:%M:%S')
    text = str(value).strip()
    return text or None


def conv_num(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace('.', '').replace(',', '.') if ',' in text else text
    try:
        return float(text)
    except ValueError:
        return None


def read_rows(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    next(rows)  # cabeçalho original

    records = []
    skipped = 0
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

        records.append({
            'regional': regional,
            'unidade': unidade,
            'frente': frente,
            'codigo_equipamento': str(cod_equip) if cod_equip is not None else None,
            'equipamento': equip,
            'codigo_operador': str(cod_op) if cod_op is not None else None,
            'operador': nome,
            'data': data,
            'hora_inicial': h_ini,
            'hora_final': h_fim,
            'codigo_operacao': str(cod_operacao) if cod_operacao is not None else None,
            'atividade': atividade,
            'classificacao': classificacao,
            'codigo_fazenda': str(cod_fazenda) if cod_fazenda is not None else None,
            'codigo_zona': str(cod_zona) if cod_zona is not None else None,
            'codigo_talhao': str(cod_talhao) if cod_talhao is not None else None,
            'fazenda': fazenda,
            'horimetro_inicial': conv_num(hor_ini),
            'horimetro_final': conv_num(hor_fim),
            'horimetro_secundario': conv_num(hor_sec),
            'velocidade_media': conv_num(vel_media),
        })
    return records, skipped


def import_to_supabase(records, supabase_url, service_key):
    endpoint = f'{supabase_url.rstrip("/")}/rest/v1/{TABLE_NAME}'
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }
    total = len(records)
    for start in range(0, total, BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]
        resp = requests.post(endpoint, headers=headers, json=batch, timeout=60)
        if resp.status_code >= 300:
            raise RuntimeError(f'Erro ao inserir lote {start}-{start+len(batch)}: '
                                f'{resp.status_code} {resp.text}')
        print(f'Inseridas {min(start + BATCH_SIZE, total)}/{total} linhas...')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python scripts/import_to_supabase.py planilha.xlsx')
        sys.exit(1)

    xlsx_path = sys.argv[1]
    supabase_url = os.environ.get('SUPABASE_URL')
    service_key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not supabase_url or not service_key:
        print('Defina as variáveis de ambiente SUPABASE_URL e SUPABASE_SERVICE_KEY antes de rodar.')
        sys.exit(1)

    records, skipped = read_rows(xlsx_path)
    print(f'Linhas lidas da planilha: {len(records)} (ignoradas por dados incompletos: {skipped})')

    import_to_supabase(records, supabase_url, service_key)
    print('Importação concluída com sucesso.')
