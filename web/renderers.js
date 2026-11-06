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

  // 5. CHESS RENDERER
  const CHESS_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
  };

  let chessSelectedSquare = null; // { r, c, coord }

  window.LANArcade.registerRenderer('chess_game', function (container, view, submitAction) {
    container.textContent = '';
    const board = view.board || [];
    const mySide = view.side || 'White';
    const isWhite = mySide === 'White';
    const isMyTurn = window.LANArcade.state.isMyTurn;
    const lastMove = view.last_move || null;
    const inCheck = view.in_check || false;

    const wrapper = document.createElement('div');
    wrapper.className = 'chess-wrapper';

    // Promotion modal if pending
    const promotionModal = document.createElement('div');
    promotionModal.className = 'chess-promotion-modal hidden';
    promotionModal.setAttribute('role', 'dialog');
    promotionModal.setAttribute('aria-label', 'Pawn Promotion');
    wrapper.appendChild(promotionModal);

    const boardEl = document.createElement('div');
    boardEl.className = 'chess-board';
    boardEl.setAttribute('role', 'grid');
    boardEl.setAttribute('aria-label', 'Chessboard');

    // Display perspective: if Black, flip rows/cols so player's pieces are at bottom
    const rowIndices = isWhite ? [0, 1, 2, 3, 4, 5, 6, 7] : [7, 6, 5, 4, 3, 2, 1, 0];
    const colIndices = isWhite ? [0, 1, 2, 3, 4, 5, 6, 7] : [7, 6, 5, 4, 3, 2, 1, 0];

    for (let rIdx = 0; rIdx < 8; rIdx++) {
      const r = rowIndices[rIdx];
      for (let cIdx = 0; cIdx < 8; cIdx++) {
        const c = colIndices[cIdx];
        const coord = `${String.fromCharCode(97 + c)}${8 - r}`;
        const piece = board[r] ? board[r][c] : null;
        const isPieceWhite = piece && piece === piece.toUpperCase();
        const isPieceMine = piece && (isWhite ? isPieceWhite : !isPieceWhite);

        const sq = document.createElement('button');
        sq.className = `chess-sq ${(r + c) % 2 === 0 ? 'light' : 'dark'}`;
        sq.setAttribute('role', 'gridcell');
        sq.setAttribute('aria-label', `${coord} ${piece ? piece : 'empty'}`);

        if (piece) {
          const pSpan = document.createElement('span');
          pSpan.className = `chess-piece ${isPieceWhite ? 'white-piece' : 'black-piece'}`;
          pSpan.textContent = CHESS_UNICODE[piece] || piece;
          sq.appendChild(pSpan);
        }

        // Highlight last move
        if (lastMove && lastMove.from && lastMove.to) {
          const [fr, fc] = lastMove.from;
          const [tr, tc] = lastMove.to;
          if ((r === fr && c === fc) || (r === tr && c === tc)) {
            sq.classList.add('chess-last-move');
          }
        }

        // Highlight King in check
        if (inCheck && piece && piece.toUpperCase() === 'K' && isPieceMine) {
          sq.classList.add('chess-check');
        }

        // Highlight selected
        if (chessSelectedSquare && chessSelectedSquare.r === r && chessSelectedSquare.c === c) {
          sq.classList.add('chess-selected');
        }

        if (isMyTurn) {
          sq.addEventListener('click', function () {
            if (!chessSelectedSquare) {
              if (isPieceMine) {
                chessSelectedSquare = { r, c, coord, piece };
                sq.classList.add('chess-selected');
              }
            } else if (chessSelectedSquare.r === r && chessSelectedSquare.c === c) {
              // Clicked same square -> cancel selection
              chessSelectedSquare = null;
              sq.classList.remove('chess-selected');
            } else if (isPieceMine) {
              // Switch selection to another friendly piece
              chessSelectedSquare = { r, c, coord, piece };
              const prev = boardEl.querySelector('.chess-selected');
              if (prev) prev.classList.remove('chess-selected');
              sq.classList.add('chess-selected');
            } else {
              // Target destination square clicked!
              const fromCoord = chessSelectedSquare.coord;
              const toCoord = coord;
              const movingPiece = chessSelectedSquare.piece;
              const isPawnPromotion = movingPiece && movingPiece.toUpperCase() === 'P' && (r === 0 || r === 7);

              if (isPawnPromotion) {
                // Show promotion picker
                promotionModal.textContent = '';
                const promoTitle = document.createElement('h4');
                promoTitle.textContent = 'Promote Pawn To:';
                promotionModal.appendChild(promoTitle);

                const promoChoices = ['Q', 'R', 'B', 'N'];
                const promoLabels = { 'Q': 'Queen', 'R': 'Rook', 'B': 'Bishop', 'N': 'Knight' };
                const choicesDiv = document.createElement('div');
                choicesDiv.className = 'chess-promo-choices';

                promoChoices.forEach(choice => {
                  const pBtn = document.createElement('button');
                  pBtn.className = 'btn btn-secondary';
                  const sym = isWhite ? choice : choice.toLowerCase();
                  pBtn.textContent = `${CHESS_UNICODE[sym]} ${promoLabels[choice]}`;
                  pBtn.addEventListener('click', () => {
                    promotionModal.classList.add('hidden');
                    chessSelectedSquare = null;
                    submitAction(`${fromCoord}${toCoord}=${choice}`);
                  });
                  choicesDiv.appendChild(pBtn);
                });

                promotionModal.appendChild(choicesDiv);
                promotionModal.classList.remove('hidden');
              } else {
                chessSelectedSquare = null;
                submitAction(`${fromCoord}${toCoord}`);
              }
            }
          });
        } else {
          sq.disabled = true;
        }

        boardEl.appendChild(sq);
      }
    }

    wrapper.appendChild(boardEl);
    container.appendChild(wrapper);
  });

  // 6. WORDLE RENDERER
  let wordleCurrentInput = ''; // Tracks letters being typed before Enter

  window.LANArcade.registerRenderer('wordle', function (container, view, submitAction) {
    container.textContent = '';
    const myGuesses = view.my_guesses || [];
    const oppGuesses = view.opp_guesses || [];
    const isMyTurn = window.LANArcade.state.isMyTurn;
    const oppName = view.opponent_name || 'Opponent';

    const wrapper = document.createElement('div');
    wrapper.className = 'wordle-wrapper';

    // Dual Board Container
    const boardsRow = document.createElement('div');
    boardsRow.className = 'wordle-boards-row';

    // 1. My Board
    const myBoardSec = document.createElement('div');
    myBoardSec.className = 'wordle-board-sec';
    const myTitle = document.createElement('h4');
    myTitle.textContent = 'Your Board';
    myBoardSec.appendChild(myTitle);

    const myGrid = document.createElement('div');
    myGrid.className = 'wordle-grid';

    for (let r = 0; r < 6; r++) {
      const rowDiv = document.createElement('div');
      rowDiv.className = 'wordle-row';

      const evaluated = myGuesses[r];
      const isCurrentRow = r === myGuesses.length && isMyTurn;

      for (let c = 0; c < 5; c++) {
        const tile = document.createElement('div');
        tile.className = 'wordle-tile';

        if (evaluated) {
          const [letter, status] = evaluated[c];
          tile.textContent = letter;
          tile.classList.add(`wordle-${status}`);
        } else if (isCurrentRow && c < wordleCurrentInput.length) {
          tile.textContent = wordleCurrentInput[c];
          tile.classList.add('wordle-filled');
        } else {
          tile.classList.add('wordle-empty');
        }
        rowDiv.appendChild(tile);
      }
      myGrid.appendChild(rowDiv);
    }
    myBoardSec.appendChild(myGrid);
    boardsRow.appendChild(myBoardSec);

    // 2. Opponent Progress Board (Letters masked)
    const oppBoardSec = document.createElement('div');
    oppBoardSec.className = 'wordle-board-sec';
    const oppTitle = document.createElement('h4');
    oppTitle.textContent = `${oppName}'s Progress`;
    oppBoardSec.appendChild(oppTitle);

    const oppGrid = document.createElement('div');
    oppGrid.className = 'wordle-grid';

    for (let r = 0; r < 6; r++) {
      const rowDiv = document.createElement('div');
      rowDiv.className = 'wordle-row';
      const evaluated = oppGuesses[r];

      for (let c = 0; c < 5; c++) {
        const tile = document.createElement('div');
        tile.className = 'wordle-tile';
        if (evaluated) {
          const [, status] = evaluated[c];
          tile.textContent = '•';
          tile.classList.add(`wordle-${status}`);
        } else {
          tile.classList.add('wordle-empty');
        }
        rowDiv.appendChild(tile);
      }
      oppGrid.appendChild(rowDiv);
    }
    oppBoardSec.appendChild(oppGrid);
    boardsRow.appendChild(oppBoardSec);

    wrapper.appendChild(boardsRow);

    // Compute keyboard letter statuses
    const keyStatuses = {};
    myGuesses.forEach(g => {
      g.forEach(([letter, status]) => {
        const l = letter.toUpperCase();
        if (status === 'green') {
          keyStatuses[l] = 'green';
        } else if (status === 'yellow' && keyStatuses[l] !== 'green') {
          keyStatuses[l] = 'yellow';
        } else if (status === 'gray' && !keyStatuses[l]) {
          keyStatuses[l] = 'gray';
        }
      });
    });

    // 3. On-screen Keyboard
    const kb = document.createElement('div');
    kb.className = 'wordle-keyboard';
    const kbLayout = [
      ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
      ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
      ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫']
    ];

    kbLayout.forEach(rowKeys => {
      const kbRow = document.createElement('div');
      kbRow.className = 'wordle-kb-row';
      rowKeys.forEach(k => {
        const keyBtn = document.createElement('button');
        keyBtn.className = 'wordle-key';
        keyBtn.textContent = k;
        if (k === 'ENTER' || k === '⌫') {
          keyBtn.classList.add('wordle-key-wide');
        } else if (keyStatuses[k]) {
          keyBtn.classList.add(`wordle-${keyStatuses[k]}`);
        }

        if (isMyTurn) {
          keyBtn.addEventListener('click', () => {
            if (k === '⌫') {
              if (wordleCurrentInput.length > 0) {
                wordleCurrentInput = wordleCurrentInput.slice(0, -1);
                window.LANArcade.registerRenderer('wordle')(container, view, submitAction);
              }
            } else if (k === 'ENTER') {
              if (wordleCurrentInput.length === 5) {
                const guessToSend = wordleCurrentInput;
                wordleCurrentInput = '';
                submitAction(guessToSend);
              }
            } else if (wordleCurrentInput.length < 5) {
              wordleCurrentInput += k;
              window.LANArcade.registerRenderer('wordle')(container, view, submitAction);
            }
          });
        } else {
          keyBtn.disabled = true;
        }

        kbRow.appendChild(keyBtn);
      });
      kb.appendChild(kbRow);
    });

    wrapper.appendChild(kb);
    container.appendChild(wrapper);
  });

  // 7. 2048 RENDERER
  let game2048KeyHandlerAttached = false;
  let game2048TouchStartX = 0;
  let game2048TouchStartY = 0;

  window.LANArcade.registerRenderer('game2048', function (container, view, submitAction) {
    container.textContent = '';
    const myBoard = view.my_board || [];
    const oppBoard = view.opp_board || [];
    const myScore = view.my_score || 0;
    const oppScore = view.opp_score || 0;
    const isMyTurn = window.LANArcade.state.isMyTurn;
    const oppName = view.opponent_name || 'Opponent';

    const wrapper = document.createElement('div');
    wrapper.className = 'g2048-wrapper';

    // Score & Header Row
    const headerRow = document.createElement('div');
    headerRow.className = 'g2048-header';

    const scoreCard = document.createElement('div');
    scoreCard.className = 'g2048-score-box';
    const scoreLabel = document.createElement('span');
    scoreLabel.className = 'score-label';
    scoreLabel.textContent = 'SCORE';
    const scoreVal = document.createElement('span');
    scoreVal.className = 'score-val';
    scoreVal.textContent = String(myScore);
    scoreCard.appendChild(scoreLabel);
    scoreCard.appendChild(scoreVal);
    headerRow.appendChild(scoreCard);

    if (oppBoard && oppBoard.length > 0) {
      const oppCard = document.createElement('div');
      oppCard.className = 'g2048-score-box opp-box';
      const oppLabel = document.createElement('span');
      oppLabel.className = 'score-label';
      oppLabel.textContent = oppName;
      const oppVal = document.createElement('span');
      oppVal.className = 'score-val';
      oppVal.textContent = String(oppScore);
      oppCard.appendChild(oppLabel);
      oppCard.appendChild(oppVal);
      headerRow.appendChild(oppCard);
    }
    wrapper.appendChild(headerRow);

    // Main 4x4 Grid
    const grid = document.createElement('div');
    grid.className = 'g2048-grid';
    grid.setAttribute('role', 'grid');
    grid.setAttribute('aria-label', '2048 Grid');

    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 4; c++) {
        const val = myBoard[r] ? myBoard[r][c] : 0;
        const tile = document.createElement('div');
        tile.className = 'g2048-tile';
        if (val > 0) {
          tile.textContent = val;
          tile.classList.add(`g2048-val-${Math.min(val, 2048)}`);
        } else {
          tile.classList.add('g2048-empty');
        }
        grid.appendChild(tile);
      }
    }
    wrapper.appendChild(grid);

    // On-screen D-Pad Controls for touch/mouse
    const dpad = document.createElement('div');
    dpad.className = 'g2048-dpad';

    const upBtn = document.createElement('button');
    upBtn.className = 'btn btn-secondary g2048-btn g2048-up';
    upBtn.textContent = '▲ (W)';
    upBtn.setAttribute('aria-label', 'Slide Up');
    if (isMyTurn) upBtn.addEventListener('click', () => submitAction('W'));
    else upBtn.disabled = true;

    const leftBtn = document.createElement('button');
    leftBtn.className = 'btn btn-secondary g2048-btn g2048-left';
    leftBtn.textContent = '◀ (A)';
    leftBtn.setAttribute('aria-label', 'Slide Left');
    if (isMyTurn) leftBtn.addEventListener('click', () => submitAction('A'));
    else leftBtn.disabled = true;

    const downBtn = document.createElement('button');
    downBtn.className = 'btn btn-secondary g2048-btn g2048-down';
    downBtn.textContent = '▼ (S)';
    downBtn.setAttribute('aria-label', 'Slide Down');
    if (isMyTurn) downBtn.addEventListener('click', () => submitAction('S'));
    else downBtn.disabled = true;

    const rightBtn = document.createElement('button');
    rightBtn.className = 'btn btn-secondary g2048-btn g2048-right';
    rightBtn.textContent = '▶ (D)';
    rightBtn.setAttribute('aria-label', 'Slide Right');
    if (isMyTurn) rightBtn.addEventListener('click', () => submitAction('D'));
    else rightBtn.disabled = true;

    dpad.appendChild(upBtn);
    const dpadMid = document.createElement('div');
    dpadMid.className = 'g2048-dpad-mid';
    dpadMid.appendChild(leftBtn);
    dpadMid.appendChild(downBtn);
    dpadMid.appendChild(rightBtn);
    dpad.appendChild(dpadMid);
    wrapper.appendChild(dpad);

    // Touch Swipe Support
    grid.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      game2048TouchStartX = touch.clientX;
      game2048TouchStartY = touch.clientY;
    }, { passive: true });

    grid.addEventListener('touchend', (e) => {
      if (!isMyTurn) return;
      const touch = e.changedTouches[0];
      const dx = touch.clientX - game2048TouchStartX;
      const dy = touch.clientY - game2048TouchStartY;
      const absDx = Math.abs(dx);
      const absDy = Math.abs(dy);

      if (Math.max(absDx, absDy) > 30) {
        if (absDx > absDy) {
          submitAction(dx > 0 ? 'D' : 'A');
        } else {
          submitAction(dy > 0 ? 'S' : 'W');
        }
      }
    }, { passive: true });

    // Keyboard controls (Arrow keys & WASD)
    if (!game2048KeyHandlerAttached) {
      game2048KeyHandlerAttached = true;
      window.addEventListener('keydown', (e) => {
        if (window.LANArcade.state.currentGameId !== 'game2048') return;
        if (!window.LANArcade.state.isMyTurn) return;
        if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

        const k = e.key.toUpperCase();
        if (k === 'ARROWUP' || k === 'W') {
          e.preventDefault();
          submitAction('W');
        } else if (k === 'ARROWLEFT' || k === 'A') {
          e.preventDefault();
          submitAction('A');
        } else if (k === 'ARROWDOWN' || k === 'S') {
          e.preventDefault();
          submitAction('S');
        } else if (k === 'ARROWRIGHT' || k === 'D') {
          e.preventDefault();
          submitAction('D');
        }
      });
    }

    container.appendChild(wrapper);
  });

  // 8. SNAKE & LADDERS RENDERER
  const LADDERS = { 1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100 };
  const SNAKES = { 16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78 };
  const DICE_FACES = ['', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];

  window.LANArcade.registerRenderer('snake_and_ladder', function (container, view, submitAction) {
    container.textContent = '';
    const positions = view.positions || {};
    const players = view.players || [];
    const isMyTurn = window.LANArcade.state.isMyTurn;
    const lastRoll = view.last_roll || 1;

    const wrapper = document.createElement('div');
    wrapper.className = 'snl-wrapper';

    // Summary & Dice Controls Bar
    const controlsBar = document.createElement('div');
    controlsBar.className = 'snl-controls';

    const diceBtn = document.createElement('button');
    diceBtn.className = 'btn btn-primary btn-lg snl-dice-btn';
    diceBtn.setAttribute('aria-label', 'Roll Dice');
    const diceIcon = DICE_FACES[lastRoll] || '🎲';
    const diceIconSpan = document.createElement('span');
    diceIconSpan.className = 'snl-dice-icon';
    diceIconSpan.textContent = diceIcon;
    const rollTextSpan = document.createElement('span');
    rollTextSpan.textContent = 'ROLL DIE';
    diceBtn.appendChild(diceIconSpan);
    diceBtn.appendChild(rollTextSpan);

    if (isMyTurn) {
      diceBtn.classList.add('snl-active-roll');
      diceBtn.addEventListener('click', () => submitAction('roll'));
    } else {
      diceBtn.disabled = true;
    }
    controlsBar.appendChild(diceBtn);

    // Positions tracker
    const tracker = document.createElement('div');
    tracker.className = 'snl-tracker';
    players.forEach((p, idx) => {
      const pos = positions[p.id] || 1;
      const tag = document.createElement('div');
      tag.className = `snl-track-item snl-p${idx + 1}`;
      tag.textContent = `${p.name} (P${idx + 1}): Sq ${pos}`;
      tracker.appendChild(tag);
    });
    controlsBar.appendChild(tracker);
    wrapper.appendChild(controlsBar);

    // 10x10 Board Grid (Squares 100 down to 1)
    const boardEl = document.createElement('div');
    boardEl.className = 'snl-board';
    boardEl.setAttribute('role', 'grid');
    boardEl.setAttribute('aria-label', 'Snake and Ladder Board');

    // Generate squares in boustrophedon order (row 10: 100-91, row 9: 81-90, etc.)
    for (let row = 9; row >= 0; row--) {
      const isEvenRow = (row % 2 === 1);
      const cols = [];
      for (let col = 0; col < 10; col++) {
        const sqNum = isEvenRow ? (row * 10 + (10 - col)) : (row * 10 + (col + 1));
        cols.push(sqNum);
      }

      cols.forEach(sqNum => {
        const cell = document.createElement('div');
        cell.className = 'snl-cell';
        cell.setAttribute('role', 'gridcell');

        const numSpan = document.createElement('span');
        numSpan.className = 'snl-sq-num';
        numSpan.textContent = sqNum;
        cell.appendChild(numSpan);

        if (LADDERS[sqNum]) {
          cell.classList.add('snl-ladder');
          const badge = document.createElement('span');
          badge.className = 'snl-feature-badge ladder-badge';
          badge.textContent = `▲${LADDERS[sqNum]}`;
          cell.appendChild(badge);
        } else if (SNAKES[sqNum]) {
          cell.classList.add('snl-snake');
          const badge = document.createElement('span');
          badge.className = 'snl-feature-badge snake-badge';
          badge.textContent = `▼${SNAKES[sqNum]}`;
          cell.appendChild(badge);
        }

        // Place player tokens on square
        const tokensDiv = document.createElement('div');
        tokensDiv.className = 'snl-tokens';
        players.forEach((p, idx) => {
          if ((positions[p.id] || 1) === sqNum) {
            const token = document.createElement('span');
            token.className = `snl-token snl-token-p${idx + 1}`;
            token.textContent = `P${idx + 1}`;
            tokensDiv.appendChild(token);
          }
        });
        cell.appendChild(tokensDiv);

        boardEl.appendChild(cell);
      });
    }

    wrapper.appendChild(boardEl);
    container.appendChild(wrapper);
  });
})();
