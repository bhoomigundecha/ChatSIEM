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
