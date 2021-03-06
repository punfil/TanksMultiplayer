#ifndef FOR_THREAD_H
#define FOR_THREAD_H
#ifndef PROJECTILE_H
#include "projectile.h"
#endif

#ifndef TANK_H
#include "tank.h"
#endif

#ifndef SINGLY_LINKED_LIST_H
#include "singly_linked_list.h"
#endif

#ifndef WHOLE_WORLD_H
#include "whole_world.h"
#endif

struct for_thread {
	int player_id;
    struct tank* tank;
    struct projectile** projectiles;
    int* csocket;
    struct sockaddr_in* client;
    bool* running;
    int* players_count;
    struct whole_world* whole_world;
    int* player_ids;
};

struct for_thread* for_thread_alloc();

void for_thread_set_values(struct for_thread* self, int player_id, struct tank* tank, struct projectile** projectiles_in_game, int* csocket, struct sockaddr_in* client, int* players_count, struct whole_world* whole_world, int* player_ids);

void for_thread_free(struct for_thread* self);

struct for_connection_handler_thread{
    int map_number;
    bool* running;
};

struct for_connection_handler_thread* for_connection_handler_thread_alloc();

void for_connection_handler_thread_set_values(struct for_connection_handler_thread* self, int map_number);

void for_connection_handler_thread_free(struct for_connection_handler_thread* self);

#endif