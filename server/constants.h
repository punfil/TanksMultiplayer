#ifndef CONSTANTS_H
#define CONSTANT_H

#define PORT 2137
#define MAX_PLAYERS 4
#define MAX_PROJECTILES 64

#define UPDATE 'u'
#define CREATE 'n'
#define TANK 't'
#define PROJECTILE 'p'
#define NOOWNER -1 //For projectiles - they need information who is owner. Tanks don't.
#define PROJECTILE_HP_ALIVE 1

#define WINDOW_WIDTH 800
#define WINDOW_HEIGHT 600
#define BACKGROUND_SCALE 50
#define USED_ID -1


#endif