# Bot de lembretes do Telegram no Discord

Este bot acompanha alguns canais do Telegram e manda uma DM no Discord quando encontra algo que você pediu para lembrar.

Cada pessoa cadastra os próprios lembretes e recebe uma DM quando uma publicação combina com eles.

## Como funciona

1. Um administrador conecta a conta do Telegram ao bot.
2. O administrador escolhe quais canais públicos do Telegram serão acompanhados.
3. Cada usuário cadastra seus lembretes com `/lembretes add`.
4. Quando uma publicação combina com um lembrete, o bot envia uma DM para o usuário.

Por padrão, o bot só verifica publicações que tenham um link `https://`.

Um grupo pode ter mais de um texto. Nesse caso, todos precisam aparecer na mesma publicação. Por exemplo, um grupo com `notebook` e `cupom` só combina com mensagens que tenham os dois textos.


## Requisitos

- Python 3.14 ou mais recente
- [uv](https://github.com/astral-sh/uv)
- Um bot criado no Discord
- Uma conta do Telegram com credenciais de API

## Instalação

Clone o projeto e instale as dependências:

```bash
git clone <repository-url>
cd discord_telegram_bot
uv sync
```

Crie um arquivo `.env` na raiz do projeto:

```env
ENVIRONMENT=development
DISCORD_TOKEN=seu_token_do_discord
TELEGRAM_API_ID=seu_api_id
TELEGRAM_API_HASH=seu_api_hash
```

O token do bot pode ser criado no [Discord Developer Portal](https://discord.com/developers/applications). As credenciais do Telegram ficam em [my.telegram.org](https://my.telegram.org/apps).

Depois, execute:

```bash
uv run main.py
```

## Primeira configuração

### 1. Conecte o Telegram

Use `/telegram login` no Discord e leia o QR Code com o aplicativo do Telegram.

Se a conta usa autenticação em dois fatores, informe a senha no parâmetro opcional `senha`. Esse comando só pode ser usado por administradores.

### 2. Adicione os canais

Os canais do Telegram também são gerenciados por administradores:

- `/canais add canal:<link|username|id>`
- `/canais rm canal:<link|username|id>`
- `/canais ls`

Apenas canais públicos podem ser adicionados. Se a conta ainda não participa do canal, o bot entra nele e tenta arquivá-lo e silenciá-lo. Se a conta já participa, as configurações existentes do Telegram não são alteradas.

Remover um canal apenas interrompe o monitoramento: a conta continua inscrita e as configurações do Telegram são preservadas.

### 3. Crie um lembrete

Qualquer usuário pode criar os próprios lembretes:

```text
/lembretes add texto:notebook
```

Isso cria um grupo chamado `notebook`. Para juntar vários textos no mesmo grupo, informe o nome do grupo:

```text
/lembretes add texto:notebook grupo:promoção
/lembretes add texto:cupom grupo:promoção
```

Nesse exemplo, a DM só será enviada quando `notebook` e `cupom` aparecerem na mesma publicação.

## Comandos

### Lembretes

- `/lembretes add texto:<texto> [grupo:<nome>]` — adiciona um texto a um grupo
- `/lembretes ls [grupo:<nome>]` — mostra seus lembretes
- `/lembretes rm texto:<texto> [grupo:<nome>]` — remove um texto
- `/lembretes del grupo:<nome>` — apaga um grupo inteiro

Se o nome do grupo não for informado, o próprio texto será usado como nome. As respostas de `add`, `rm` e `del` são privadas; `ls` é público para que o usuário possa compartilhar sua configuração quando quiser.

Quando uma publicação combina com vários grupos do mesmo usuário, o bot junta tudo em uma única DM.

### Telegram e canais

Estes comandos são apenas para administradores:

- `/telegram login [senha:<senha-2FA>]`
- `/telegram status`
- `/canais add canal:<link|username|id>`
- `/canais rm canal:<link|username|id>`
- `/canais ls`

O status do Telegram responde de forma privada.

### Informações do bot

- `/info` — mostra informações sobre o bot

`/info` é restrito a administradores e responde publicamente.

## Desenvolvimento

Alguns comandos úteis:

```bash
# Instalar ou atualizar as dependências
uv sync

# Executar o bot
uv run main.py

# Verificar o código
uv run ruff check .
uv run ruff format --check .
uv run ty check

# Gerar o pacote
uv build
```

Com `ENVIRONMENT=development`, o bot usa logs mais detalhados e recarrega os cogs quando os arquivos mudam. Em `production`, o hot reload fica desativado.

O filtro das publicações fica em `src/services/notifications/notifier.py`. A lógica e o armazenamento dos lembretes ficam em `src/database/reminders.py`.

## Estrutura do projeto

```text
src/
├── cogs/              # Comandos do Discord
├── database/          # Canais e lembretes no SQLite
├── services/
│   ├── discord/       # Cliente do Discord
│   ├── notifications/ # Verificação dos lembretes e envio das DMs
│   └── telegram/      # Cliente e login do Telegram
└── shared/            # Código compartilhado
```

## Mantenedores

- [@jhgaldino](https://github.com/jhgaldino)
- [@DanGM96](https://github.com/DanGM96)
