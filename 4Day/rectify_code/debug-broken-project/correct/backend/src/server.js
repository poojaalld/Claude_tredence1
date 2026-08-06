const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const users = {
  learner: "pass123",
  demo: "claude"
};

app.post("/login", (req, res) => {
  const { userId, password } = req.body;
  if (!userId || !password) {
    return res.status(400).json({ error: "Enter both user ID and password." });
  }

  const isValidUser = users[userId] === password;
  if (!isValidUser) {
    return res.status(401).json({ error: "Invalid credentials." });
  }

  return res.json({ message: "Sign in successful" });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Auth backend listening on port ${PORT}`);
});
