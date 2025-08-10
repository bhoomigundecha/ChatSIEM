// what do we need 
// 1. <h1> Lottery <h1> 
// This changes based on a condition 
// jab jab naya kuch render hoga we need to check if the sum is 15

import { useState } from "react"

// if the sum is 15, then we need to render <h1> Lottery, Congrats you have won the ticker  <h1>

export default function Lottery() {
    const [currnum, setcurrnum] = useState("555")
    
    const helper = () =>{
        let num = Math.floor(Math.random() * 1000).toString().padStart(3, "0");
        setcurrnum(num.toString());
    }

    const checksum = (currnum) =>{
        let sum = 0;
        for(let i = 0; i < currnum.length; i++){
            sum += parseInt(currnum[i]);
        }
        return sum
    }
    return(
        <div className="main">
            {
                checksum(currnum) === 15 ? (
                    <h1> Lottery, Congrats you have won the ticket </h1>) :
                    (<h1> Lottery </h1>)
            }
            <p> Lottery Ticket = {currnum} </p>
            <button onClick={helper}> Get New Ticket </button>

        </div>
    )
}