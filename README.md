## Bot de Integração Discord-Telegram

Este bot permite integrar mensagens de um canal do Telegram com um servidor do Discord.

Este bot foi desenvolvido para acompanhar canais de promoções no Telegram e enviar novas mensagens para um servidor do Discord. Por isso ele possui um filtro que somente envia mensagens que contenham links de promoções. Se quiser você pode remover o filtro e usar o bot para acompanhar qualquer canal do Telegram.

### Requisitos

Python 3.6 ou superior instalado

Conta no Discord

Conta no Telegram

## Passo 1: Clone o Repositório

Clone o repositório do projeto para sua máquina local

## Passo 2: Crie uma Aplicação no Telegram

Para usar a API do Telegram, você precisa criar um aplicativo Telegram. Siga as etapas abaixo para criar um aplicativo Telegram e obter as credenciais necessárias para usar a API do Telegram.

Crie uma conta no Telegram se você ainda não tiver uma.

Visite o site do Telegram para desenvolvedores e faça login com sua conta do Telegram.

Clique em Criar aplicativo Telegram.

Preencha os detalhes do aplicativo e clique em Criar aplicativo.

Você verá o API ID e o API Hash do seu aplicativo. Anote-os, pois você precisará deles mais tarde.

## Passo 2: Crie um Bot no Discord


Crie uma conta no Discord se você ainda não tiver uma.

Visite o Portal de Desenvolvedores do Discord e faça login com sua conta do Discord.

Clique em Novo aplicativo e dê um nome ao seu aplicativo.

Clique em Bot no menu lateral esquerdo e clique em Adicionar bot.

Você verá o token de autenticação do seu bot.

Clique em OAuth2 no menu lateral esquerdo e marque a caixa de seleção bot na seção Scopes.

Marque as caixas de seleção Send Messages e Read Message History na seção Bot Permissions.

Marque as caixas de seleção Presence Intent e Server Members Intent na seção Privileged Gateway Intents.

Clique no link gerado em Scopes e adicione o bot ao seu servidor do Discord.



## Passo 2: Configure as Variáveis de Ambiente

Crie um arquivo .env na raiz do projeto, seguindo o exemplo do arquivo .env.example.

## Passo 3 (Opcional): Configure um Ambiente Virtual

É recomendável configurar um ambiente virtual para isolar as dependências deste projeto. Para isso, navegue até a pasta raiz do projeto onde você clonou o repositório e execute o seguinte comando:

- Windows (cmd):
  - `python3 -m venv venv && venv\Scripts\activate.bat`
- Windows (PowerShell):
  - `python3 -m venv venv && venv\Scripts\Activate.ps1`
- macOS / Linux:
  - `python3 -m venv venv && source venv/bin/activate`

Você verá o nome do ambiente virtual aparecendo no seu prompt de comando, indicando que o ambiente está ativo.

## Passo 3: Instale as Dependências

Instale as dependências Python necessárias executando o seguinte comando na raiz do projeto:
```
pip install -r requirements.txt
```
## Passo 4: Inicie o Bot do Discord
Execute o bot do Discord com o seguinte comando:

```
python main.py
```

O bot será iniciado e tentará conectar automaticamente ao Telegram se já existir uma sessão válida. Caso contrário, você precisará fazer login usando o comando `/login` no Discord.

## Passo 5: Login no Telegram

O login no Telegram é feito através do Discord usando QR code:

1. No servidor do Discord onde o bot está instalado, execute o comando `/login`
2. O bot enviará uma imagem com um QR code (privada, apenas você pode ver)
3. Abra o aplicativo Telegram no seu celular
4. Vá em **Configurações** > **Dispositivos** > **Conectar dispositivo por QR code**
5. Escaneie o QR code exibido no Discord
6. Se sua conta tiver autenticação de dois fatores (2FA), use o comando `/login senha:sua_senha` para fornecer a senha

**Notas importantes:**
- O comando `/login` é privado (ephemeral) - apenas você pode ver o QR code e as mensagens
- Se você já estiver logado, o bot informará seu status atual
- Se o QR code expirar, execute `/login` novamente para gerar um novo
- O bot tentará reconectar automaticamente na próxima inicialização se a sessão ainda for válida

## Passo 6: Verificação de Novas Mensagens

No servidor do Discord onde o bot está instalado, verifique se o bot está online. Você verá o status do bot como online.
Verifique as novas mensagens no Telegram. Se houver novas mensagens, o bot as enviará para o servidor do Discord.
Teste os comandos do bot no servidor do Discord para garantir que tudo esteja funcionando corretamente.

## Comandos Disponíveis

Todos os comandos estão dispoíveis usando barra (slash) no Discord. Procure pelo bot na lateral esquerda da barra de comandos. Alguns deles são privados e apenas o dono do bot pode usar. Como `/status` para verificar o status do bot.
