#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>

//Networking
#include <sys/socket.h>
#include <unistd.h>
#include <arpa/inet.h>

#include "for_thread.h"


struct for_thread* for_thread_alloc(){
    struct for_thread* self;
    self = (struct for_thread*)malloc(sizeof(struct for_thread));
    self->running = (bool*)malloc(sizeof(bool));
    if (self == NULL){
        return NULL;
    }
    memset(self, 0, sizeof(struct for_thread*));
    return self;
}

void for_thread_set_values(struct for_thread* self, int player_id, struct tank* tank, struct projectile** projectiles_in_game, int* csocket, struct sockaddr_in* client, int* players_count, struct whole_world* whole_world, int* player_ids){
    self->player_id = player_id;
    self->tank = tank;
    self->projectiles = projectiles_in_game;
    self->csocket = csocket;
    self->client = client;
    self->players_count = players_count;
    *self->running = true;
    self->whole_world = whole_world;
    self->player_ids = player_ids;
}

void for_thread_free(struct for_thread* self){
    free(self->running);
    free(self);
}

struct for_connection_handler_thread* for_connection_handler_thread_alloc(){
    struct for_connection_handler_thread* self;
    self = (struct for_connection_handler_thread*)malloc(sizeof(struct for_connection_handler_thread));
    self->running = (bool*)malloc(sizeof(bool));
    if (self == NULL){
        return NULL;
    }
    memset(self, 0, sizeof(struct for_connection_handler_thread*));
    return self;
}

void for_connection_handler_thread_set_values(struct for_connection_handler_thread* self, int map_number){
    *self->running = true;
    self->map_number = map_number;
}

void for_connection_handler_thread_free(struct for_connection_handler_thread* self){
    free(self->running);
    free(self);
}