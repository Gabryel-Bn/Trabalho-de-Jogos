"""Neon Tetris - Trabalho 2 de Jogos Digitais."""
import random
from pathlib import Path
import pygame
from grid import Grid, obj

pygame.init(); pygame.font.init()
WIDTH,HEIGHT,FPS=800,600,60
screen=pygame.display.set_mode((WIDTH,HEIGHT));pygame.display.set_caption("Neon Tetris - Trabalho 2")
clock=pygame.time.Clock()
INK,PAPER=(20,21,39),(244,240,226);WHITE=(255,255,255);PINK=(255,64,137);CYAN=(37,211,194);YELLOW=(255,215,68)
COLORS={"I":CYAN,"O":YELLOW,"T":(161,102,255),"S":(75,210,105),"Z":(255,78,94),"J":(55,132,245),"L":(255,145,54)}
SHAPES={"I":[[1,1,1,1]],"O":[[1,1],[1,1]],"T":[[0,1,0],[1,1,1]],"S":[[0,1,1],[1,1,0]],
        "Z":[[1,1,0],[0,1,1]],"J":[[1,0,0],[1,1,1]],"L":[[0,0,1],[1,1,1]]}
SMALL=pygame.font.Font(None,20);FONT=pygame.font.Font(None,28);BIG=pygame.font.Font(None,49);LOGO=pygame.font.Font(None,64)


class Piece:
    def __init__(self,name=None):
        self.name=name or random.choice(list(SHAPES));self.shape=[r[:] for r in SHAPES[self.name]]
        self.color=COLORS[self.name];self.x=(10-len(self.shape[0]))//2;self.y=-1
    def rotated(self): return [list(row) for row in zip(*self.shape[::-1])]


class Button(obj):
    def __init__(self,rect,label,action,color=WHITE): self.rect,self.label,self.action,self.color=pygame.Rect(rect),label,action,color
    def update(self,dt): pass
    def draw(self):
        hover=self.rect.collidepoint(pygame.mouse.get_pos());pygame.draw.rect(screen,INK,self.rect.move(4,4),border_radius=4)
        rect=self.rect.move(-2,-2) if hover else self.rect;pygame.draw.rect(screen,self.color,rect,border_radius=4);pygame.draw.rect(screen,INK,rect,3,border_radius=4)
        image=FONT.render(self.label,True,INK);screen.blit(image,image.get_rect(center=rect.center))


class DuckAnimation(obj):
    """Objeto com sprites que reage ao jogo e troca de imagem para animar."""
    def __init__(self):
        super().__init__(0,0)
        folder=Path(__file__).parent/"images"/"duck";self.images={};self.timer=0
        for name in ("base","blink","wing","quack","step","crouch"):
            image=pygame.image.load(folder/f"{name}.png").convert_alpha();scale=105/max(image.get_size())
            self.images[name]=pygame.transform.smoothscale(image,(int(image.get_width()*scale),int(image.get_height()*scale)))
    def update(self,dt): self.timer+=dt
    def draw(self,state,clearing):
        if state=="gameover": name="crouch"
        elif clearing: name="wing" if int(self.timer*9)%2 else "quack"
        elif state=="paused": name="blink"
        else: name="step" if int(self.timer*3)%2 else "base"
        image=self.images[name];screen.blit(image,image.get_rect(center=(105,226+int(4*pygame.math.Vector2(0,1).rotate(self.timer*120).y))))


class Tetris:
    def __init__(self):
        self.grid=Grid(275,50,(10,20),25);self.duck=DuckAnimation()
        self.buttons=[Button((35,430,52,42),"←","left"),Button((96,430,52,42),"↻","rotate",CYAN),Button((157,430,52,42),"→","right"),
                      Button((96,481,52,42),"↓","down"),Button((35,538,174,39),"SOLTAR","drop",YELLOW),Button((585,482,180,44),"PAUSAR","pause",CYAN)]
        self.state="start";self.reset_values()
    def reset_values(self):
        self.grid.reset();self.piece,self.next_piece=Piece(),Piece();self.score=self.lines=0;self.level=1
        self.last_fall=pygame.time.get_ticks();self.clear_rows=[];self.clear_until=0
    def start(self): self.reset_values();self.state="playing"
    def move(self,dx,dy=0):
        if self.state=="playing" and not self.clear_rows and self.grid.valid(self.piece,dx=dx,dy=dy): self.piece.x+=dx;self.piece.y+=dy;return True
        return False
    def rotate(self):
        if self.state!="playing" or self.clear_rows:return
        shape=self.piece.rotated()
        for nudge in (0,-1,1,-2,2):
            if self.grid.valid(self.piece,shape,dx=nudge):self.piece.shape=shape;self.piece.x+=nudge;break
    def fall(self):
        if not self.move(0,1):self.lock()
    def drop(self):
        if self.state!="playing" or self.clear_rows:return
        distance=0
        while self.move(0,1):distance+=1
        self.score+=distance*2;self.lock()
    def lock(self):
        if self.state!="playing":return
        above=self.grid.lock(self.piece);rows=self.grid.full_lines()
        if rows:self.clear_rows=rows;self.clear_until=pygame.time.get_ticks()+420;self.score+=[0,100,300,500,800][len(rows)]*self.level;self.lines+=len(rows);self.level=self.lines//10+1
        self.piece,self.next_piece=self.next_piece,Piece()
        if above or not self.grid.valid(self.piece):self.state="gameover"
    def action(self,action):
        if action=="pause":
            if self.state=="playing":self.state="paused"
            elif self.state=="paused":self.state="playing"
        elif action=="left":self.move(-1)
        elif action=="right":self.move(1)
        elif action=="down":self.fall()
        elif action=="rotate":self.rotate()
        elif action=="drop":self.drop()
    def event(self,event):
        if event.type==pygame.KEYDOWN:
            if self.state in ("start","gameover") and event.key in (pygame.K_RETURN,pygame.K_SPACE):self.start()
            elif event.key==pygame.K_LEFT:self.action("left")
            elif event.key==pygame.K_RIGHT:self.action("right")
            elif event.key==pygame.K_DOWN:self.action("down")
            elif event.key==pygame.K_UP:self.action("rotate")
            elif event.key==pygame.K_SPACE:self.action("drop")
            elif event.key in (pygame.K_p,pygame.K_ESCAPE):self.action("pause")
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            if self.state in ("start","gameover") and pygame.Rect(310,315,180,48).collidepoint(event.pos):self.start()
            else:
                for button in self.buttons:
                    if button.rect.collidepoint(event.pos):self.action(button.action)
    def update(self,dt):
        now=pygame.time.get_ticks();self.duck.update(dt)
        if self.clear_rows and now>=self.clear_until:self.grid.clear_lines(self.clear_rows);self.clear_rows=[]
        if self.state=="playing" and not self.clear_rows and now-self.last_fall>max(100,750-(self.level-1)*65):self.fall();self.last_fall=now
    def text(self,value,font,color,pos,center=False):
        image=font.render(str(value),True,color);screen.blit(image,image.get_rect(center=pos) if center else pos)
    def card(self,rect,title,value,color=WHITE):
        pygame.draw.rect(screen,INK,pygame.Rect(rect).move(5,5),border_radius=5);pygame.draw.rect(screen,color,rect,border_radius=5);pygame.draw.rect(screen,INK,rect,3,border_radius=5)
        self.text(title,SMALL,INK,(rect[0]+12,rect[1]+10));self.text(value,BIG,INK,(rect[0]+12,rect[1]+34))
    def draw(self):
        screen.fill(PAPER)
        for x in range(0,WIDTH,25):pygame.draw.line(screen,(232,228,214),(x,0),(x,HEIGHT))
        for y in range(0,HEIGHT,25):pygame.draw.line(screen,(232,228,214),(0,y),(WIDTH,y))
        self.text("TRAB 2 • ARCADE",SMALL,INK,(35,37));self.text("NEON",LOGO,INK,(30,55));self.text("TETRIS",LOGO,PINK,(30,105));self.duck.draw(self.state,bool(self.clear_rows))
        status="FIM DE JOGO" if self.state=="gameover" else "PAUSADO" if self.state=="paused" else "COMBO!" if self.clear_rows else "CIDADE ACESA!"
        self.text(status,FONT,INK,(35,294));self.text("Setas: mover e girar",SMALL,INK,(35,326));self.text("Espaço: soltar • P: pausa",SMALL,INK,(35,348))
        for b in self.buttons[:5]:b.draw()
        self.grid.draw(screen,self.piece if self.state=="playing" else None,self.clear_rows,int(pygame.time.get_ticks()/80)%2==0)
        self.card((570,50,195,95),"PONTOS",f"{self.score:06d}",PINK);self.card((570,165,90,85),"NÍVEL",self.level,YELLOW);self.card((675,165,90,85),"LINHAS",self.lines)
        pygame.draw.rect(screen,WHITE,(570,270,195,175),border_radius=5);pygame.draw.rect(screen,INK,(570,270,195,175),3,border_radius=5);self.text("PRÓXIMA PEÇA",SMALL,INK,(584,284))
        ox=625+(4-len(self.next_piece.shape[0]))*12;oy=330+(3-len(self.next_piece.shape))*12
        for y,row in enumerate(self.next_piece.shape):
            for x,value in enumerate(row):
                if value:pygame.draw.rect(screen,self.next_piece.color,(ox+x*25,oy+y*25,23,23),border_radius=3)
        self.buttons[5].label="CONTINUAR" if self.state=="paused" else "PAUSAR";self.buttons[5].draw()
        if self.state in ("start","paused","gameover"):
            shade=pygame.Surface((250,500),pygame.SRCALPHA);shade.fill((20,21,39,220));screen.blit(shade,(275,50));title={"start":"NEON TETRIS","paused":"PAUSADO","gameover":"FIM DE JOGO"}[self.state]
            self.text(title,BIG,WHITE,(400,240),True);subtitle="Complete linhas!" if self.state=="start" else "Pressione P" if self.state=="paused" else f"Você fez {self.score} pontos";self.text(subtitle,SMALL,WHITE,(400,285),True)
            if self.state!="paused":
                rect=pygame.Rect(310,315,180,48);pygame.draw.rect(screen,YELLOW,rect,border_radius=4);self.text("JOGAR" if self.state=="start" else "JOGAR DE NOVO",FONT,INK,rect.center,True)

    def run(self):
        """Encapsula o loop principal: entrada, atualização e desenho."""
        running=True
        while running:
            dt=clock.tick(FPS)/1000
            for event in pygame.event.get():
                if event.type==pygame.QUIT:running=False
                else:self.event(event)
            self.update(dt);self.draw();pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Tetris().run()
