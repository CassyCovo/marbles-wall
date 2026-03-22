# Marbles Wall

A large-scale generative artwork where falling, stacking, and fading marbles visualize missing people data across a multi-screen RAMPs display.

## Mission
This project transforms missing persons data into an immersive visual experience. Each marble represents an individual, and as they accumulate, the visualization highlights the growing magnitude and emotional weight of those who are missing.

Rather than focusing on individual identities, the work emphasizes scale, absence, and accumulation—inviting viewers to reflect on the collective impact of missing persons cases.

## Data
This project is inspired by publicly available missing persons data from the National Missing and Unidentified Persons System (NamUs).

Due to the sensitive nature of this data, the repository includes only anonymized sample data that preserves structural patterns without exposing personal information.

Source: https://www.namus.gov/MissingPersons/Search

## Features
- Physics-based marble simulation  
- Collision and stacking behavior  
- Multi-screen rendering using MPI  
- Generative, data-driven visualization  

## Tech Stack
- Python  
- pygame  
- mpi4py  

## How to Run
```bash
mpirun -np 20 python marbles_wall.py
