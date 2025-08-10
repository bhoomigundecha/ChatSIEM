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