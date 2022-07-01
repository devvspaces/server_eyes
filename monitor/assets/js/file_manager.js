// Code for file manager management

function Manager() {
    this.boards = [];
    this.current_board = null;
    this.addBoard = function(board){
        this.boards.push(board)
    }
    this.setCurrentBoard = function(index){
        this.current_board = index
    }
    this.getBoard = function(index){
        return this.boards[index]
    }
    this.getCurrentBoard = function(){
        
    }
    this.nextBoard = function(){
        if (this.boards.length > 0){
            index = 0
            if (this.current_board !== null){
                index = this.current_board + 1
            }
            if (this.boards.length < index + 1){
                throw 'No next board'
            }
            return this.getBoard(index)
        }
        throw 'No boards'
    }
    this.prevBoard = function(){
        if (this.boards.length > 0){
            if (this.current_board === null || this.current_board < 1){
                throw 'No previous board'
            }
            return this.getBoard(index)
        }
        throw 'No boards'
    }
    
    
}


function Board(pwd, files) {
    this.pwd = pwd
    this.files = files
}


function File(name) {
    this.name = name
}