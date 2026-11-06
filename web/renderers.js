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
})();
