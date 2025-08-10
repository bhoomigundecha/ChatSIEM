### Module 1
REACT : JS library for creating UI

Babel converts jsx to js 

Setting up local environment with Vite.js

Vite.js is comparitively faster 

Command : npm create vite@latest 

import, export 
(when you need to return a single value)
***import Title from "./Title.jsx"***
***export default Title***

(otherwise)
***import {Title} from "./Title.jsx"***
***export {Title}***

Rules(for writing markup)
1. Return a single root element 
2. Close all tags
3. camelCase most of the things 

React Fragment : Lets you group multiple components into a single entity (<> </>)

JSX in curly braces : It becomes javascript
eg. ***<p> 2*2 = {2*2} </p>***

eg. ***let name = "bhoomi"***
***<p> {name} </p>***

eg.

suppose classname cc 

function cc{
    return(
        <div className="cc">
            <h1>hello</h1>
        </div>
    )
}

this would be in our css 
***
.cc{
    border : 1px solid black
}
***


### Module 2

React props : Props are the information that you pass to a JSX tag


eg. 
***<Title name="bhoomi" age="20"/>***

eg. 
<Product title="phone" price=30k/>

export default function Product({title, product}){
    return(
        <div className="Product">
            <h4>{Title}</h4>
        </div>
    )
}

Passing arrays to props 

Option 1 :
import Product from './Product.js'

function ProductTab(){
    let options=["hi-tech","durable","fast"]

    return(
        <>
        <Product title="phone" price={30000} features={options}/>
        </>
    )
}

Option 2 : 

return(
    <>
    <Product title="phone" price={30000} features={{a:"hi-tech"}}/>
    </>
)


Rendering array(using map)

function ProductTab(){
    let options=["hi-tech","durable","fast"]

    return(
        <>
        <Product title="phone" price={30000} features={options}/>
        </>
    )
}

function Product({title, price, features}){
    const list = features.map((feature)=><li>{feature}</li>)

    // this way wo direct list wise add hoga
    return(
        <div className="Product">
            <h1>{title}</h1>
            <p>{list}<p>
        </div>
    )
}


Conditionals

Adding elements on the basis of some conditions 

{price>=1000 ? <p>Discount : 5% </p> : <p>Price : {price}</p>}

Dynamic Component Styling(Styling decided at runtime)

(styles defined inside the function itself)

function Product({title, price, features}){
    let styles = {backgroundColor : "blue"};
    let styles = {backgroundColor : price>3000?"yellow" : "red"};
    return(
        <div className="Product" style={styles}>
            <h1>{title}</h1>
        </div>
    )
}

Practice example 1 : Show a Hello Message to the user in different color 

function Hello({userName, textColor}){
    return(
        <>
        <h1 style={{color:textColor}}>Hello {userName}</h1>
        </>
    )
}
export default App(){
    return(
        <>
        <Hello userName="BHOOMI" textColor="red"/>
        <Hello userName="GITHUB" textColor="green"/>
        </>
    )
}


Practice Example 2 : Building Amazon Cards 
(Added in product tab)

### Module 3 

Handling onClick events 

function printHello(){
    console.log("Hello!")
}

export default function Button(){
    return(
        <button onClick={printHello}>Click </button>
    )
}

Handling nonClick events

function handleHover(){
    console.log("Hovered")
}

export default function Button(){
    return(
        <button onMouseOver={handleHover}>Click </button>
    );
}

Form submit 

function handleFormSubmit(event){
    event.preventDefault();
    console.log("Form submitted")
}
export default function Form(){
    return(
        <form onSubmit={handleFormSubmit}>
            <input type="text" />
            <button type="submit">Submit</button>
        </form>
    );
}

React has 4 main pillars (State, Components, Hooks, Props)

### States in React 

(DOM mei bhi update karne hote hai, jiske liye state use hota hai)

(Re-render hona chahiye basically)
(Re-execute hoga and updated changes apply ho jayenge)


### Hooks in React 
Lets us use react features without writing a class
Hooks can only be called in side function component


1. useState() : react hook that lets us add a state variable to our component (re-render mei help karta hai)

const [state, setState] = useState(initialStatevalue)

useState always returns an array with exactly two values

setState re render ko trigger karata hai 

Practice : Create Like button (Toggle : Like Unlike)


import React from "react"
import { useState } from "react"
function LikeButton(){
    const [isliked, setisliked] = useState(false)
    const handleLiked = () =>{
        setisliked(!isliked)
    }
    return(
        <div>
            <p onClick={handleLiked}> 
                {isliked ? (
                    <i className="fa-solid fa-heart"></i>
                ) : (
                    <i className="fa-regular fa-heart"></i>
                )}
            </p>
        </div>
    )
}

export default LikeButton


**Re-render : How does it work ? **

setState jabhi call hoga pura function re execute hoga 

setStates are async methods 

eg. 
let incCount() =>{
    setCount(count+1)
    setCount(count+1)
}

the value of count should increase by 1, but it does not, because setCount are async functions 

but this would work 

let incCount(){
    setCount((currCount)=>{
        return currCount+1;
    })
    setCount({currCount}=>{
        return currCount+1;
    })
}

this would increase the count by 2 

More about State : 
Re-render tabhi hoga jab state variable mei change aayega 

Jab state variable mei change hoga(actual change of variable) tabhi hi change hoga 

example : 
let [count, setCount] = useState(init())
abh jabhi bhi re render hoga init call hoga wapas 
but it wont make a difference to useState kyuki wo bas first time initialisation ke time kaam aata hai 

let [count,setCount] = useState(init)
this is better kyuki now the function does not get executed on re rendering


### Objects in States 

suppose hum useState mei object ya array pass karte hai, to hume use karna padta hai spread operator, kyuki changes detect nhi hote(arrays address pr chakta hai index mei change detect hi nahi hota)

toh when we use spread operator , it creates a new object and then it gets updated

eg. 

toh spread aise karte hai 
***setMoves({...moves, blue : moves.blue+1})***
            Spread Value     Updated in spread


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

### Arrays in States 

setArr([..arr, "new element added in the back"])

Practice : Create a ToDoList 


import { useState } from "react";
export default function ToDoList(){
    let [todos, settodos] = useState(["sample tasks"])
    let [newtodo, setnewTodo] = useState("")
    let addNewTask = (e) =>{
        e.preventDefault() // prevent the page from refreshing
        settodos([...todos, newtodo])
        setnewTodo("")
    }
    let updatearray=(event)=>{
        setnewTodo(event.target.value)

    };
    return(
        <div className="main">
            <h4> TO DO LIST </h4>
            <form>
                <input type="text" name="task" placeholder="Enter a task" value={newtodo} onChange={updatearray}/>
                <button onClick={addNewTask}>Add Task</button>

                <br></br><br></br>
                <h4> TODOLIST </h4>
                <ul>
                    {
                        todos.map((todo)=><li>{todo}</li>)
                    }
                </ul>
            </form>
        </div>
    )
}

### Unique Key for List items 

It is a better idea to create an array of objects each having a unique id 

let [todos, settodos] = useState([{task:"sample-task", id:uuidv4()}])
    let [newtodo, setnewTodo] = useState("")
    let addNewTask = (e) =>{
        e.preventDefault()
        settodos([...todos, {task : newtodo, id:uuidv4()}])
        setnewTodo("")
    }
    let updatearray=(event)=>{
        setnewTodo(event.target.value)

    };

    let deletetodo=(id)=>{

    }
    return(
        <div className="main">
            <h4> TO DO LIST </h4>
            <form>
                <input type="text" name="task" placeholder="Enter a task" value={newtodo} onChange={updatearray}/>
                <button onClick={addNewTask}>Add Task</button>

                <br></br><br></br>
                <h4> TODOLIST </h4>
                <ul>
                    {
                        todos.map((todo)=><li key={todo.id}><span>{todo.task}</li>)
                    }
                </ul>
            </form>
        </div>
    )

### Deleting from Arrays 

filter is used to delete element in React 

import { useState } from "react";
import {v4 as uuidv4} from 'uuid';
export default function ToDoList(){
    let [todos, settodos] = useState([{task:"sample-task", id:uuidv4()}])
    let [newtodo, setnewTodo] = useState("")
    let addNewTask = (e) =>{
        e.preventDefault()
        settodos([...todos, {task : newtodo, id:uuidv4()}])
        setnewTodo("")
    }
    let updatearray=(event)=>{
        setnewTodo(event.target.value)

    };
    let deletetodo=(id)=>{
       
        const updatedTodos = todos.filter((todo) => todo.id !== id);
        settodos(updatedTodos);

    };
    return(
        <div className="main">
            <h4> TO DO LIST </h4>
            <form>
                <input type="text" name="task" placeholder="Enter a task" value={newtodo} onChange={updatearray}/>
                <button onClick={addNewTask}>Add Task</button>

                <br></br><br></br>
                <h4> TODOLIST </h4>
                <ul>
                    {
                        todos.map((todo)=><li key={todo.id}><span>{todo.task}</span><button onClick={() => deletetodo(todo.id)}>delete</button>
</li>)
                    }
                </ul>
            </form>
        </div>
    )
}


### Updating elements in array 

***Updating all elements in array*** 

let UpperCaseAll = () =>{
    setTasks((prevTasks)=>{
        prevTasks.map((todo)=>{
            return{
                ...todo,
                task:todo.task.toUpperCase()
            };
        })
    })
}

***Updating one element in array***

let updateOneTask = (id) => {
    setTasks((prevTasks)=>{
        prevTasks.map(todo)=>{
            if(todo.id===id){
                return{
                    ...todo,
                    tasks :todo.tasks.toUpperCase()
                }
            }
            else{
                return todo;
            }
        }
    })
}

Practice : Mark as Done feature in ToDoList 

import { useState } from "react";
import { v4 as uuidv4 } from 'uuid';

export default function ToDoList() {
    const [todos, setTodos] = useState([{ task: "sample-task", id: uuidv4(), isDone: false }]);
    const [newtodo, setNewTodo] = useState("");

    const addNewTask = (e) => {
        e.preventDefault();
        if (newtodo.trim() === "") return;
        setTodos([...todos, { task: newtodo, id: uuidv4(), isDone: false }]);
        setNewTodo("");
    };

    const updatearray = (event) => {
        setNewTodo(event.target.value);
    };

    const deleteTodo = (id) => {
        setTodos(todos.filter((todo) => todo.id !== id));
    };

    const markdone = (id) => {
        setTodos((prevTodos) => {
            return prevTodos.map((todo) => {
                if (todo.id === id) {
                    return { ...todo, isDone: !todo.isDone };
                } else {
                    return todo;
                }
            });
        });
    };

    return (
        <div className="main">
            <h4> TO DO LIST </h4>
            <form onSubmit={addNewTask}>
                <input
                    type="text"
                    name="task"
                    placeholder="Enter a task"
                    value={newtodo}
                    onChange={updatearray}
                />
                <button type="submit">Add Task</button>

                <br /><br />
                <h4> TODOLIST </h4>
                <ul>
                    {todos.map((todo) => (
                        <li key={todo.id}>
                            <span style={{ textDecoration: todo.isDone ? "line-through" : "none" }}>
                                {todo.task}
                            </span>
                            <button type="button" onClick={() => deleteTodo(todo.id)}>delete</button>
                            {todo.isDone
                                ? <i className="fa-regular fa-square-check" onClick={() => markdone(todo.id)}></i>
                                : <i className="fa-regular fa-square" onClick={() => markdone(todo.id)}></i>
                            }
                        </li>
                    ))}
                </ul>
            </form>
        </div>
    );
}


Practice : Lottery Question 

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




















