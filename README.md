# Bot de Integração Discord-Telegram v2

Bot que integra mensagens de canais do Telegram com servidores do Discord, desenvolvido para aprendizado e desenvolvimento de skills.

## Funcionalidades

- 🔄 **Hot-reload automático** de extensões (cogs) durante desenvolvimento
- 🔐 **Autenticação via QR Code** para Telegram com suporte a 2FA
- 📨 **Filtro inteligente** que envia apenas mensagens com links de promoções
- ⚡ **Inicialização paralela** do bot Discord e cliente Telegram para melhor performance
- 🎯 **Comandos slash** modernos usando `app_commands`
- 🛡️ **Tratamento robusto de erros** com cleanup automático de recursos
- 📊 **Comandos de status** para monitorar o estado do bot e conexões

## Arquitetura

O projeto segue uma arquitetura modular e desacoplada:

- **`src/services/discord/`** - Cliente Discord com hot-reload de cogs
- **`src/services/telegram/`** - Cliente Telegram com autenticação QR
- **`src/cogs/`** - Extensões modulares (comandos organizados por grupo)
- **`src/shared/`** - Código compartilhado entre serviços
- **`src/config.py`** - Gerenciamento centralizado de configuração e inicialização

### Características Técnicas

- **Inicialização paralela**: Bot Discord e cliente Telegram são inicializados simultaneamente usando `asyncio.gather()`
- **Type safety**: Tipagem completa com type hints e validação em tempo de execução
- **Cleanup automático**: Recursos são limpos automaticamente mesmo em caso de erro
- **Factory pattern**: Uso de métodos `create_and_initialize()` para criação consistente de instâncias

## Requisitos

- Python 3.10 ou superior
- Conta no Discord com bot criado
- Conta no Telegram com API credentials

## Instalação

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd discord_telegram_bot
```

### 2. Configure o Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
DISCORD_TOKEN=seu_token_do_discord
TELEGRAM_API_ID=seu_api_id
TELEGRAM_API_HASH=seu_api_hash
TELEGRAM_CHANNELS=canal1,canal2
DISCORD_CHANNEL_IDS=123456789,987654321
```

**Como obter as credenciais:**

- **Discord Token**: [Discord Developer Portal](https://discord.com/developers/applications) > Seu App > Bot > Token
- **Telegram API**: [Telegram API](https://my.telegram.org/apps) > API development tools

### 5. Execute o Bot

```bash
python main.py
```

O bot inicializará ambos os serviços (Discord e Telegram) em paralelo. Se já houver uma sessão válida do Telegram, a conexão será automática.

## Uso

### Login no Telegram

O login é feito através do Discord usando QR code:

1. Execute o comando `/telegram login` no Discord
2. Escaneie o QR code exibido com o app Telegram
3. Se tiver 2FA, use `/telegram login senha:sua_senha`

### Comandos Disponíveis

Todos os comandos são **slash commands** (barra `/`):

- `/info` - Informações sobre o bot
- `/telegram login` - Fazer login no Telegram via QR code
- `/reminders` - Gerenciar lembretes (ver subcomandos)

Alguns comandos são privados e apenas o dono do bot pode usar.

### Hot-reload durante Desenvolvimento

Durante o desenvolvimento, as extensões (cogs) são recarregadas automaticamente quando você salva alterações nos arquivos. Isso acelera significativamente o ciclo de desenvolvimento.

## Estrutura do Projeto

```
discord_telegram_bot/
├── src/
│   ├── cogs/             # Extensões modulares (comandos)
│   ├── services/
│   │   ├── discord/      # Cliente Discord
│   │   ├── integration/  # Integração entre Discord e Telegram
│   │   └── telegram/     # Cliente Telegram
│   ├── shared/           # Código compartilhado
│   └── config.py         # Configuração e inicialização
├── main.py               # Ponto de entrada
└── requirements.txt      # Dependências
```

## Desenvolvimento

### Adicionando Novos Comandos

1. Crie um novo arquivo em `src/cogs/` ou adicione ao cog existente
2. Use `commands.GroupCog` para organizar comandos em grupos
3. O hot-reload detectará automaticamente as mudanças

### Modificando o Filtro de Mensagens

O filtro está em `src/services/integration/forwarder.py`. Por padrão, apenas mensagens com links são encaminhadas. Modifique o método `_filter()` para alterar o comportamento.

## Referências

Este projeto foi desenvolvido seguindo as melhores dicas do [Discord.py Masterclass Guide](https://fallendeity.github.io/discord.py-masterclass/), que fornece diretrizes sobre arquitetura, organização de código e padrões de design para bots Discord.

## Mantenedores

- [@jhgaldino](https://github.com/jhgaldino) - Idealização e desenvolvimento
- [@DanGM96](https://github.com/DanGM96) - Desenvolvimento, arquitetura e contribuições
