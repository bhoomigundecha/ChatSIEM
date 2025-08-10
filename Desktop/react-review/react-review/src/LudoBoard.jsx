import { useState } from "react"

export default function LudoBoard(){
    let [moves, setMoves] = useState({green:0, red:0, blue:0, yellow:0})

    let updateBlue = () =>{
        setMoves({...moves,blue: moves.blue+1})
    };
    let updateYellow = () =>{
        setMoves({...moves,yellow: moves.yellow+1})
    };
    let updateGreen = () =>{
        setMoves({...moves,green: moves.green+1})
    };
    let updateRed = () =>{
        setMoves({...moves,red: moves.red+1})
    };
    return(
        <div className="main">
            <div className="board">
                <p> Game Begins </p>
                <p> Blue moves = {moves.blue}</p>
                <button style={{backgroundColor:"blue"}} onClick={updateBlue}> {moves.blue} </button>
                <p> Yellow moves = {moves.yellow}</p>
                <button style={{backgroundColor:"yellow"}} onClick={updateYellow}> {moves.yellow} </button>
                <p> Green moves = {moves.green}</p>
                <button style={{backgroundColor:"green"}} onClick={updateGreen}> {moves.green} </button>
                <p> Red moves = {moves.red}</p>
                <button style={{backgroundColor:"red"}} onClick={updateRed}> {moves.red} </button>
            </div>
        </div>
    )
}