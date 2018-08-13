#ifndef NODE_H
#define NODE_H

#include <vector>
#include <list>

using namespace std;

// ***************************************************************************
struct node{
  bool active;
  bool blocked;
  int dist;
  vector<int> adj;
  list<int> B;

  node(){
    active = true;
    blocked = false;
    dist = -1;
    B.clear();
  }
};


#endif
#pragma once
