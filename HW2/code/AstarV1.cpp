#include <iostream>
#include <vector>
#include <queue>
#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
#include <set>

using namespace std;
using Coord = pair<int,int>;
using State = pair<Coord, int>;

const int LMIN = 2;
const int LMAX = 4;

int heuristic(const State& a, const State& b) {
    // Manhattan distance (ignore length in heuristic)
    return abs(a.first.first - b.first.first) +
           abs(a.first.second - b.first.second);
}

vector<State> getNeighbors(const State& s, int grid_size) {
    vector<State> neighbors;

    int x = s.first.first;
    int y = s.first.second;
    int L = s.second;

    vector<Coord> directions = {
        {1,0}, {-1,0}, {0,1}, {0,-1}
    };

    for (auto d : directions) {
        int nx = x + d.first;
        int ny = y + d.second;

        if (nx >= 0 && nx < grid_size &&
            ny >= 0 && ny < grid_size) {

            int newL = L + 1;
            if (newL > LMAX)
                newL = LMIN;

            neighbors.push_back({{nx, ny}, newL});
        }
    }

    return neighbors;
}

void reconstructPath(
    map<State, State>& came_from,
    State current,
    set<State>& path_states)
{
    while (came_from.find(current) != came_from.end()) {
        path_states.insert(current);
        current = came_from[current];
    }
    path_states.insert(current);
}

void aStar(State start_state,
           State goal_state,
           int grid_size,
           set<State>& occupancy_grid,
           set<State>& path_states)
{
    using PQElement = pair<int, State>; // (f_score, state)
    priority_queue<PQElement,
                   vector<PQElement>,
                   greater<PQElement>> open_set;

    open_set.push({heuristic(start_state, goal_state), start_state});

    map<State, State> came_from;
    map<State, int> g_score;

    g_score[start_state] = 0;

    while (!open_set.empty()) {

        State current = open_set.top().second;
        open_set.pop();

        if (current == goal_state) {
            reconstructPath(came_from, current, path_states);
            cout << "Path found.\n";
            return;
        }

        vector<State> neighbors = getNeighbors(current, grid_size);

        for (auto& neighbor : neighbors) {

            if (occupancy_grid.count(neighbor))
                continue;

            int tentative_g = g_score[current] + 1;

            if (!g_score.count(neighbor) ||
                tentative_g < g_score[neighbor]) {

                came_from[neighbor] = current;
                g_score[neighbor] = tentative_g;

                int f_score = tentative_g +
                              heuristic(neighbor, goal_state);

                open_set.push({f_score, neighbor});
            }
        }
    }

    cout << "No path found.\n";
}

int main(void){

    int grid_size = 4;

    State start_state = {{0, 0}, LMIN};
    State goal_state  = {{3, 3}, LMIN};

    set<State> occupancy_grid;
    set<State> path_states;

    aStar(start_state, goal_state, grid_size,
          occupancy_grid, path_states);

    cout << "Path states:\n";
    for (auto& s : path_states) {
        cout << "("
             << s.first.first << ", "
             << s.first.second << ", "
             << s.second << ")\n";
    }

    return 0;
}