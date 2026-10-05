import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");

  // -----------------------------------------
  // LOAD TASKS FROM DATABASE
  // -----------------------------------------

  const loadTasks = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/tasks"
      );

      if (!response.ok) {
        throw new Error("Could not load tasks");
      }

      const data = await response.json();

      setTasks(data.tasks || []);
      setError("");

    } catch (err) {
      console.error("Error loading tasks:", err);

      setError(
        "Could not load saved tasks. Make sure the backend is running."
      );
    }
  };


  // -----------------------------------------
  // LOAD TASKS WHEN WEBSITE OPENS
  // -----------------------------------------

  useEffect(() => {
    loadTasks();
  }, []);


  // -----------------------------------------
  // UPLOAD AND ANALYZE IMAGE
  // -----------------------------------------

  const handleFileChange = async (event) => {
  const selectedFile = event.target.files[0];

  if (!selectedFile) {
    return;
  }

  setFile(selectedFile);
  setError("");
  setUploading(true);

  const formData = new FormData();
  formData.append("file", selectedFile);

  const isPdf = selectedFile.type === "application/pdf";

  const endpoint = isPdf
    ? "http://127.0.0.1:8000/analyze-pdf"
    : "http://127.0.0.1:8000/analyze-image";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("AI analysis failed");
    }

    const data = await response.json();

    console.log("AI result:", data);

    if (data.error) {
      setError(data.error);
      return;
    }

    await loadTasks();
  } catch (err) {
    console.error("Upload error:", err);

    setError(
      "Could not analyze the file. Make sure the backend is running."
    );
  } finally {
    setUploading(false);
  }
};

  // -----------------------------------------
  // COMPLETE TASK
  // -----------------------------------------

  const completeTask = async (taskId) => {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${taskId}/complete`,
        {
          method: "PUT",
        }
      );

      if (!response.ok) {
        throw new Error("Could not complete task");
      }

      // Reload tasks after completing
      await loadTasks();

    } catch (err) {

      console.error("Complete task error:", err);

      setError(
        "Could not complete the task."
      );
    }
  };


  // -----------------------------------------
  // DELETE TASK
  // -----------------------------------------

  const deleteTask = async (taskId) => {

    const confirmed = window.confirm(
      "Are you sure you want to delete this task?"
    );

    if (!confirmed) {
      return;
    }

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${taskId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Could not delete task");
      }

      // Reload tasks after deleting
      await loadTasks();

    } catch (err) {

      console.error("Delete task error:", err);

      setError(
        "Could not delete the task."
      );
    }
  };


  // -----------------------------------------
  // WEBSITE
  // -----------------------------------------

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div>

          <h1>
            LifeAdmin AI
          </h1>

          <p>
            Your AI assistant for everyday life
          </p>

        </div>

      </header>


      {/* MAIN */}

      <main className="main">

        {/* HERO */}

        <section className="hero">

          <h2>
            Turn messy information into action.
          </h2>

          <p>
            Upload a screenshot and LifeAdmin AI will
            find important tasks, deadlines, reminders,
            appointments, and events automatically.
          </p>


          {/* UPLOAD BOX */}

          <div className="upload-box">

            <div className="upload-icon">
              📄
            </div>


            <h3>

              {uploading
                ? "🤖 LifeAdmin AI is analyzing..."
                : "Upload screenshot or pdf to get started"}

            </h3>


            <p>
              Upload a screenshot or pdf containing important information.
            </p>


            <label className="upload-button">

              {uploading
                ? "Analyzing..."
                : "Choose File"}

              <input
                type="file"
                onChange={handleFileChange}
                hidden
                accept=".png,.jpg,.jpeg,.pdf"
                disabled={uploading}
              />

            </label>


            {/* SELECTED FILE */}

            {file && (

              <p className="selected-file">
                📎 {file.name}
              </p>

            )}


            {/* ERROR */}

            {error && (

              <div className="error-message">

                ❌ {error}

              </div>

            )}

          </div>

        </section>


        {/* TASKS */}
        <section className="stats">
  <div className="stat-card">
    <span className="stat-number">{tasks.length}</span>
    <span className="stat-label">Total Tasks</span>
  </div>

  <div className="stat-card">
    <span className="stat-number">
      {tasks.filter((task) => task.status !== "completed").length}
    </span>
    <span className="stat-label">Pending</span>
  </div>

  <div className="stat-card">
    <span className="stat-number">
      {tasks.filter((task) => task.status === "completed").length}
    </span>
    <span className="stat-label">Completed</span>
  </div>
</section>

        <section className="tasks">

          <div className="tasks-header">

            <div>

              <h2>
                My Tasks
              </h2>

              <p>
                {tasks.length} task
                {tasks.length !== 1 ? "s" : ""} saved
              </p>

            </div>

          </div>


          {/* EMPTY STATE */}

          {tasks.length === 0 && !error && (

            <div className="empty-state">

              <div className="empty-icon">
                📋
              </div>

              <h3>
                No tasks yet
              </h3>

              <p>
                Upload a screenshot or pdf and LifeAdmin AI
                will find your tasks automatically.
              </p>

            </div>

          )}


          {/* TASK CARDS */}

          {tasks.map((task) => (

            <div
              className={`task-card ${
                task.status === "completed"
                  ? "completed-task"
                  : ""
              }`}
              key={task.id}
            >

              <div className="task-content">

                <h3>
                  {task.title}
                </h3>


                <p>
                  📅 {task.date}
                </p>


                <p>
                  🕐 {task.time}
                </p>


                <p className="task-reason">
                  💡 {task.reason}
                </p>


                {/* STATUS */}

                {task.status === "completed" && (

                  <p className="completed-label">
                    ✅ Completed
                  </p>

                )}

              </div>


              {/* RIGHT SIDE */}

              <div className="task-actions">

                <span
                  className={`priority ${
                    task.priority.toLowerCase()
                  }`}
                >
                  {task.priority}
                </span>


                {/* COMPLETE BUTTON */}

                {task.status !== "completed" && (

                  <button
                    className="complete-button"
                    onClick={() =>
                      completeTask(task.id)
                    }
                  >
                    ✓ Complete
                  </button>

                )}


                {/* DELETE BUTTON */}

                <button
                  className="delete-button"
                  onClick={() =>
                    deleteTask(task.id)
                  }
                >
                  🗑 Delete
                </button>

              </div>

            </div>

          ))}

        </section>

      </main>

    </div>
  );
}

export default App;