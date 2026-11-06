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
})();
