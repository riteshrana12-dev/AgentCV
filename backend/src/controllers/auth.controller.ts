import { Request, Response } from "express";
import jwt from "jsonwebtoken";
import z from "zod";
import bcrypt from "bcrypt";
import client from "../config/prismaClient";

const authSchema = z.object({
  email: z.email({ message: "Email is not in correct format" }),
  password: z
    .string({ message: "password lenght of 6-9 character" })
    .min(6)
    .max(9),
});

export const signup = async (req: Request, res: Response) => {
  try {
    console.log(req);
    const pasredData = authSchema.safeParse(req.body);

    if (!pasredData.success) {
      return res.status(400).json({ error: pasredData.error.issues });
    }

    const { email, password } = pasredData.data;

    const existingUser = await client.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      return res.status(400).json({
        message: "user with this email already exists",
        existingUser,
      });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const userCreated = await client.user.create({
      data: {
        email,
        hashedPassword,
      },
    });

    const token = jwt.sign(
      {
        userid: userCreated.id,
        email: userCreated.email,
      },
      process.env.JWT_SECRET as string,
    );

    res.cookie("token", token, {
      httpOnly: true, // prevents JS access
      secure: false, // only over HTTPS
      sameSite: "lax",
    });

    if (userCreated) {
      return res.status(200).json({
        success: true,
        message: "Account created",
        userCreated: userCreated,
        token: token,
      });
    } else {
      return res.status(404).json({
        success: false,
        message: "Account creation failed , Please try again later",
      });
    }
  } catch (err: any) {
    return res.status(500).json({
      success: false,
      message: err.message,
    });
  }
};

export const signin = async (req: Request, res: Response) => {
  try {
    const pasredData = authSchema.safeParse(req.body);

    if (!pasredData.success) {
      return res.status(400).json({ error: pasredData.error.issues });
    }

    const { email, password } = pasredData.data;

    const checkUserExist = await client.user.findUnique({
      where: { email },
    });

    if (!checkUserExist) {
      return res.status(400).json({
        success: false,
        message: "No user found with this email",
      });
    }

    const verifyPassword = await bcrypt.compare(
      password,
      checkUserExist.hashedPassword,
    );

    if (!verifyPassword) {
      return res.status(400).json({
        success: false,
        message: "Incorrect password",
      });
    }

    const token = jwt.sign(
      {
        userid: checkUserExist.id,
        email: checkUserExist.email,
      },
      process.env.JWT_SECRET as string,
    );

    res.cookie("token", token, {
      httpOnly: true, // prevents JS access
      secure: false, // only over HTTPS
      sameSite: "lax",
    });

    return res.status(200).json({
      success: true,
      message: "Sign in successful",
      token: token,
    });
  } catch (err: any) {
    return res.status(500).json({
      success: false,
      message: err.message,
    });
  }
};

export const signout = async (req: Request, res: Response) => {
  try {
    res.clearCookie("token", {
      httpOnly: true,
      secure: false,
      sameSite: "lax",
      path: "/", // must match the path used when setting the cookie
    });

    return res.status(200).json({ message: "Logged out successfully" });
  } catch (err: any) {
    return res.status(500).json({
      success: false,
      message: err.message,
    });
  }
};
