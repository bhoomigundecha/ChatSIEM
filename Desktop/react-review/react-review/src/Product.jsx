import React from "react";
import "./App.css"
function Product({title, properties, priceOld, priceNew}) {
    let props = properties.map((property)=><li>{property}</li>)
    return (
        <div className="product">
            <div className="part1">
                <h4>{title}</h4>
                <ul>
                    {props}
                </ul>
            </div>
            <div className="part2">
                <p><s>{priceOld}</s> {priceNew}</p>
            </div>

        </div>
    );
}

export default Product;