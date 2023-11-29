# discord_telegram_bot
Bot de discord agregador de mensagem de canais no telegram

Bot de Integração Discord-Telegram
Este bot permite integrar mensagens de um canal do Telegram com um servidor do Discord.

Requisitos
Python 3.6 ou superior instalado
Conta no Discord
Conta no Telegram
Passo 1: Clone o Repositório
Clone o repositório do projeto para sua máquina local:

bash
Copy code
git clone https://github.com/seu-usuario/seu-projeto.git
Passo 2: Configure as Variáveis de Ambiente
As seguintes variáveis de ambiente precisam ser configuradas para o funcionamento do bot:

TELEGRAM_API_ID: Seu API ID do Telegram. Você pode obter isso seguindo as instruções em API development tools.
TELEGRAM_API_HASH: Sua API Hash do Telegram. Você pode obter isso seguindo as instruções em API development tools.
DISCORD_TOKEN: Token de autenticação do seu bot no Discord. Você pode criar um bot no Portal de Desenvolvedores do Discord e obter o token lá.
TELEGRAM_CHANNELS: Uma lista de nomes de usuário de canais do Telegram separados por vírgulas que você deseja monitorar. Por exemplo, canal1,canal2,canal3.
Você pode configurar essas variáveis de ambiente no seu sistema ou criar um arquivo .env na raiz do projeto e definir as variáveis lá.
