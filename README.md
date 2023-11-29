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

As seguintes variáveis de ambiente precisam ser configuradas para o funcionamento do bot:

TELEGRAM_API_ID: Seu API ID do Telegram.

TELEGRAM_API_HASH: Sua API Hash do Telegram. 

DISCORD_TOKEN: Token de autenticação do seu bot no Discord. Você pode criar um bot no Portal de Desenvolvedores do Discord e obter o token.

TELEGRAM_CHANNELS: Uma lista de canais do Telegram separados por vírgulas que você deseja monitorar. Por exemplo, canal1,canal2,canal3.

Você pode configurar essas variáveis de ambiente no seu sistema ou criar um arquivo .env na raiz do projeto e definir as variáveis lá.

## Passo 3: Configure um Ambiente Virtual e Instale as Dependências

É recomendável configurar um ambiente virtual para isolar as dependências deste projeto. Siga os passos abaixo para criar e ativar um ambiente virtual:

Navegue até a pasta raiz do projeto onde você clonou o repositório.

Crie um ambiente virtual executando o seguinte comando:


```
python -m venv venv
```

Isso criará uma pasta chamada venv no diretório do projeto, que conterá todas as dependências isoladas.

Ative o ambiente virtual:

No Windows:

```
venv\Scripts\activate.bat
```
### Obs : Se você estiver usando o PowerShell ou Windows 11, execute o seguinte comando em vez disso:

```
venv\Scripts\Activate.ps1
```
No macOS e Linux:

```
source venv/bin/activate
```
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
O bot será iniciado e estará pronto para responder a comandos no servidor do Discord.

## Passo 5: Inicie a Verificação de Novas Mensagens

No servidor do Discord onde o bot está instalado, você pode usar o comando ```!start``` para iniciar a verificação de novas mensagens nos canais do Telegram configurados. O bot enviará novas mensagens do Telegram para o canal correspondente no Discord.