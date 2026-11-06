/**
 * Native graphical board renderers for LAN Arcade (Phase 2).
 * Each renderer produces the EXACT same action string the terminal accepts.
 */

(function () {
  'use strict';

  if (!window.LANArcade) return;

  // 1. TIC-TAC-TOE RENDERER
  window.LANArcade.registerRenderer('tic_tac_toe', function (container, view, submitAction) {
    container.textContent = ''; // Safe clear
    const board = view.board || [];
    const winningLine = new Set(view.winning_line || []);
    const isMyTurn = window.LANArcade.state.isMyTurn;

    const grid = document.createElement('div');
    grid.className = 'ttt-grid';
    grid.setAttribute('role', 'grid');
    grid.setAttribute('aria-label', 'Tic-Tac-Toe Board');

    for (let i = 0; i < 9; i++) {
      const cellVal = board[i];
      const btn = document.createElement('button');
      btn.className = 'ttt-cell';
      btn.setAttribute('role', 'gridcell');
      btn.setAttribute('aria-label', `Cell ${i + 1}${cellVal ? ': ' + cellVal : ''}`);

      if (cellVal === 'X') {
        btn.textContent = 'X';
        btn.classList.add('x-cell', 'taken');
        btn.disabled = true;
      } else if (cellVal === 'O') {
        btn.textContent = 'O';
        btn.classList.add('o-cell', 'taken');
        btn.disabled = true;
      } else {
        btn.textContent = '';
        if (!isMyTurn) {
          btn.disabled = true;
        } else {
          btn.addEventListener('click', function () {
            submitAction(String(i + 1));
          });
        }
      }

      if (winningLine.has(i)) {
        btn.classList.add('winning-cell');
      }

      grid.appendChild(btn);
    }

    container.appendChild(grid);
  });

  // 2. CONNECT FOUR RENDERER
  window.LANArcade.registerRenderer('connect4', function (container, view, submitAction) {
    container.textContent = '';
    const board = view.board || []; // 6 rows x 7 cols
    const winningCells = new Set((view.winning_cells || []).map(cell => `${cell[0]},${cell[1]}`));
    const isMyTurn = window.LANArcade.state.isMyTurn;

    const wrapper = document.createElement('div');
    wrapper.className = 'c4-wrapper';

    // Drop buttons above columns
    const dropRow = document.createElement('div');
    dropRow.className = 'c4-drop-row';
    for (let c = 0; c < 7; c++) {
      const dropBtn = document.createElement('button');
      dropBtn.className = 'c4-drop-btn';
      dropBtn.setAttribute('aria-label', `Drop chip in column ${c + 1}`);
      dropBtn.textContent = '▼';
      const colFull = board.length > 0 && board[0][c] !== null;
      if (!isMyTurn || colFull) {
        dropBtn.disabled = true;
      } else {
        dropBtn.addEventListener('click', () => submitAction(String(c + 1)));
      }
      dropRow.appendChild(dropBtn);
    }
    wrapper.appendChild(dropRow);

    // 6x7 Grid Board
    const grid = document.createElement('div');
    grid.className = 'c4-grid';
    grid.setAttribute('role', 'grid');
    grid.setAttribute('aria-label', 'Connect Four Board');

    for (let r = 0; r < 6; r++) {
      for (let c = 0; c < 7; c++) {
        const cell = document.createElement('div');
        cell.className = 'c4-cell';
        cell.setAttribute('role', 'gridcell');

        const chip = document.createElement('div');
        chip.className = 'c4-chip';
        const val = board[r] ? board[r][c] : null;

        if (val === 'X') {
          chip.classList.add('c4-x');
        } else if (val === 'O') {
          chip.classList.add('c4-o');
        } else {
          chip.classList.add('c4-empty');
        }

        if (winningCells.has(`${r},${c}`)) {
          chip.classList.add('c4-win');
        }

        cell.appendChild(chip);

        // Clicking anywhere in the column also drops in that column
        if (isMyTurn && !(board[0] && board[0][c] !== null)) {
          cell.style.cursor = 'pointer';
          cell.addEventListener('click', () => submitAction(String(c + 1)));
        }

        grid.appendChild(cell);
      }
    }

    wrapper.appendChild(grid);
    container.appendChild(wrapper);
  });

  // 3. MEMORY MATCH RENDERER
  let memorySelectedCard = null; // Local selection state for picking 2 cards

  window.LANArcade.registerRenderer('memory_match', function (container, view, submitAction) {
    container.textContent = '';
    const rows = view.rows || 4;
    const cols = view.cols || 4;
    const board = view.board || [];
    const matchedCoords = new Set((view.matched || []).map(c => `${c[0]},${c[1]}`));
    const lastReveal = view.last_reveal || null;
    const isMyTurn = window.LANArcade.state.isMyTurn;

    const wrapper = document.createElement('div');
    wrapper.className = 'memory-wrapper';

    // Scores summary bar
    const scoreboard = document.createElement('div');
    scoreboard.className = 'memory-scoreboard';
    const players = view.players || [];
    const scores = view.scores || {};
    players.forEach(p => {
      const pScore = document.createElement('div');
      pScore.className = 'memory-score-item';
      pScore.textContent = `${p.name}: ${scores[p.id] || 0} pairs`;
      scoreboard.appendChild(pScore);
    });
    wrapper.appendChild(scoreboard);

    // Cards Grid
    const grid = document.createElement('div');
    grid.className = 'memory-grid';
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    grid.setAttribute('role', 'grid');
    grid.setAttribute('aria-label', 'Memory Match Cards');

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const coordStr = `${String.fromCharCode(65 + c)}${r + 1}`;
        const isMatched = matchedCoords.has(`${r},${c}`);
        const isRevealedCard1 = lastReveal && lastReveal.card1 && lastReveal.card1.row === r && lastReveal.card1.col === c;
        const isRevealedCard2 = lastReveal && lastReveal.card2 && lastReveal.card2.row === r && lastReveal.card2.col === c;
        const faceSymbol = (board[r] && board[r][c]) ||
          (isRevealedCard1 ? lastReveal.card1.symbol : (isRevealedCard2 ? lastReveal.card2.symbol : null));

        const card = document.createElement('button');
        card.className = 'memory-card';
        card.setAttribute('role', 'gridcell');
        card.setAttribute('aria-label', `Card ${coordStr}`);

        const inner = document.createElement('div');
        inner.className = 'memory-card-inner';

        const front = document.createElement('div');
        front.className = 'memory-card-front';
        front.textContent = coordStr; // Back of card shows coordinate

        const back = document.createElement('div');
        back.className = 'memory-card-back';
        back.textContent = faceSymbol || '❓'; // Front shows emoji face

        inner.appendChild(front);
        inner.appendChild(back);
        card.appendChild(inner);

        if (isMatched) {
          card.classList.add('flipped', 'matched');
          card.disabled = true;
        } else if (isRevealedCard1 || isRevealedCard2) {
          card.classList.add('flipped', 'last-reveal');
        }

        if (memorySelectedCard === coordStr) {
          card.classList.add('selected');
        }

        if (isMyTurn && !isMatched) {
          card.addEventListener('click', function () {
            if (!memorySelectedCard) {
              // First card selected
              memorySelectedCard = coordStr;
              card.classList.add('selected');
            } else if (memorySelectedCard === coordStr) {
              // Clicked same card -> deselect
              memorySelectedCard = null;
              card.classList.remove('selected');
            } else {
              // Second card selected -> submit action "A1 B2"
              const act = `${memorySelectedCard} ${coordStr}`;
              memorySelectedCard = null;
              submitAction(act);
            }
          });
        } else {
          card.disabled = true;
        }

        grid.appendChild(card);
      }
    }

    wrapper.appendChild(grid);
    container.appendChild(wrapper);
  });

  // 4. BATTLESHIP RENDERER
  window.LANArcade.registerRenderer('battleship', function (container, view, submitAction) {
    container.textContent = '';
    const myShots = view.my_shots || {};
    const oppShots = view.opp_shots || {};
    const ownGrid = view.own_grid || [];
    const isMyTurn = window.LANArcade.state.isMyTurn;
    const oppName = view.opponent_name || 'Opponent';

    const wrapper = document.createElement('div');
    wrapper.className = 'bs-wrapper';

    // 1. Radar / Target Grid (Enemy Waters)
    const targetSection = document.createElement('div');
    targetSection.className = 'bs-section';
    const targetTitle = document.createElement('h3');
    targetTitle.textContent = `🎯 Target Grid (${oppName}'s Waters)`;
    targetSection.appendChild(targetTitle);

    const targetGrid = document.createElement('div');
    targetGrid.className = 'bs-grid';

    // Header row (A-E)
    targetGrid.appendChild(document.createElement('div')); // empty corner
    for (let c = 0; c < 5; c++) {
      const colLabel = document.createElement('div');
      colLabel.className = 'bs-label';
      colLabel.textContent = String.fromCharCode(65 + c);
      targetGrid.appendChild(colLabel);
    }

    for (let r = 0; r < 5; r++) {
      const rowLabel = document.createElement('div');
      rowLabel.className = 'bs-label';
      rowLabel.textContent = String(r + 1);
      targetGrid.appendChild(rowLabel);

      for (let c = 0; c < 5; c++) {
        const coordKey = `${r},${c}`;
        const coordStr = `${String.fromCharCode(65 + c)}${r + 1}`;
        const cell = document.createElement('button');
        cell.className = 'bs-cell';
        cell.setAttribute('aria-label', `Fire at ${coordStr}`);

        if (coordKey in myShots) {
          const isHit = myShots[coordKey];
          cell.textContent = isHit ? '💥' : '🌊';
          cell.classList.add(isHit ? 'bs-hit' : 'bs-miss');
          cell.disabled = true;
        } else {
          cell.textContent = '';
          if (isMyTurn) {
            cell.classList.add('bs-fireable');
            cell.addEventListener('click', () => submitAction(coordStr));
          } else {
            cell.disabled = true;
          }
        }
        targetGrid.appendChild(cell);
      }
    }
    targetSection.appendChild(targetGrid);
    wrapper.appendChild(targetSection);

    // 2. Friendly Fleet Grid (Your Ships)
    const fleetSection = document.createElement('div');
    fleetSection.className = 'bs-section';
    const fleetTitle = document.createElement('h3');
    fleetTitle.textContent = '🛡️ Your Fleet';
    fleetSection.appendChild(fleetTitle);

    const fleetGrid = document.createElement('div');
    fleetGrid.className = 'bs-grid';

    fleetGrid.appendChild(document.createElement('div'));
    for (let c = 0; c < 5; c++) {
      const colLabel = document.createElement('div');
      colLabel.className = 'bs-label';
      colLabel.textContent = String.fromCharCode(65 + c);
      fleetGrid.appendChild(colLabel);
    }

    for (let r = 0; r < 5; r++) {
      const rowLabel = document.createElement('div');
      rowLabel.className = 'bs-label';
      rowLabel.textContent = String(r + 1);
      fleetGrid.appendChild(rowLabel);

      for (let c = 0; c < 5; c++) {
        const coordKey = `${r},${c}`;
        const cell = document.createElement('div');
        cell.className = 'bs-cell bs-fleet-cell';
        const hasShip = ownGrid[r] && ownGrid[r][c] !== null;

        if (hasShip) {
          cell.classList.add('bs-ship');
        }

        if (coordKey in oppShots) {
          const isHit = oppShots[coordKey];
          cell.textContent = isHit ? '💥' : '🌊';
          cell.classList.add(isHit ? 'bs-hit' : 'bs-miss');
        } else if (hasShip) {
          cell.textContent = '🚢';
        }

        fleetGrid.appendChild(cell);
      }
    }
    fleetSection.appendChild(fleetGrid);
    wrapper.appendChild(fleetSection);

    container.appendChild(wrapper);
  });
})();
