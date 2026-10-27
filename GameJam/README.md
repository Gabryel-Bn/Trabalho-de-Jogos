# Pulso

Protótipo de jogo 2D para Godot 4. A nave avança automaticamente. Use **Espaço** ou clique esquerdo para ativar o único comando: no chão ela salta em um arco fixo; no ar, pode dar um avanço horizontal uma vez antes de pousar. Desvie dos obstáculos e colete cristais para pontuar. Os obstáculos têm altura e distância mais consistentes, e os cristais aparecem dentro do alcance do salto. Há também uma cabeça escondida como uma lua flutuante no canto superior direito. O recorde fica salvo localmente. A cada trecho percorrido, o cenário troca de paleta e os obstáculos variam de forma. Música ambiente e efeitos sonoros são gerados pelo jogo, sem arquivos de áudio extras.

## Rodar

1. Instale o Godot 4 (versão Standard, sem .NET, é suficiente).
2. Abra o Godot, escolha **Importar** e selecione `project.godot` nesta pasta.
3. Pressione **F6** para executar a cena atual ou **F5** para executar o projeto.
4. Para editar scripts no VS Code, abra esta pasta nele. O Godot continua sendo usado para abrir cenas e executar o jogo.

## Música e nave

O jogo gera uma pequena trilha ambiente em tempo real e toca em loop. O sprite vetorial da nave fica em `assets/ship.svg` e pode ser substituído por outra arte SVG.
