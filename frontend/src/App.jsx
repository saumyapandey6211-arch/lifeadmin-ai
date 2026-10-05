import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = "https://lifeadmin-ai-usa3.onrender.com";

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const fileInputRef = useRef(null);

  const loadTasks = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`);
      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (error) {
      setMessage("Could not connect to LifeAdmin AI.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleUpload = async (event) => {
    const file = event.target.files[0];

    if (!file) {
      return;
    }

    setUploading(true);
    setMessage("LifeAdmin AI is analyzing your file...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const isPdf = file.type === "application/pdf";

      const endpoint = isPdf
        ? `${API_BASE_URL}/analyze-pdf`
        : `${API_BASE_URL}/analyze-image`;

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        setMessage(data.error || "Something went wrong while analyzing the file.");
        return;
      }

      await loadTasks();

      setMessage(
        `${data.tasks?.length || 0} actionable item${
          data.tasks?.length === 1 ? "" : "s"
        } found.`
      );
    } catch (error) {
      setMessage("Could not analyze the file. Please try again.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const completeTask = async (id) => {
    try {
      await fetch(`${API_BASE_URL}/tasks/${id}/complete`, {
        method: "PUT"
      });

      await loadTasks();
    } catch (error) {
      setMessage("Could not complete the task.");
    }
  };

  const deleteTask = async (id) => {
    try {
      await fetch(`${API_BASE_URL}/tasks/${id}`, {
        method: "DELETE"
      });

      await loadTasks();
    } catch (error) {
      setMessage("Could not delete the task.");
    }
  };

  const pendingTasks = tasks.filter(
    (task) => task.status !== "completed"
  );

  const completedTasks = tasks.filter(
    (task) => task.status === "completed"
  );

  const getPriorityClass = (priority) => {
    if (priority === "High") {
      return "priority-high";
    }

    if (priority === "Medium") {
      return "priority-medium";
    }

    return "priority-low";
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">✦</div>

          <div>
            <h1>LifeAdmin AI</h1>
            <p>Your personal life organizer</p>
          </div>
        </div>

        <div className="ai-status">
          <span className="status-dot"></span>
          AI Ready
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <div className="hero-content">
            <span className="eyebrow">AI FOR EVERYDAY LIFE</span>

            <h2>
              Turn life's clutter
              <br />
              into <span>action.</span>
            </h2>

            <p>
              Upload a screenshot or PDF. LifeAdmin AI finds the important
              tasks, deadlines, events, and reminders hiding inside it.
            </p>

            <button
              className="upload-button"
              onClick={() => fileInputRef.current.click()}
              disabled={uploading}
            >
              {uploading ? "Analyzing..." : "Upload screenshot or PDF"}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.pdf"
              onChange={handleUpload}
              hidden
            />

            <div className="supported">
              <span>✓</span>
              PNG
              <span>✓</span>
              JPG
              <span>✓</span>
              PDF
            </div>
          </div>

          <div className="hero-visual">
            <div className="floating-card card-one">
              <div className="mini-icon">📅</div>
              <div>
                <strong>Deadline found</strong>
                <small>Project submission</small>
              </div>
            </div>

            <div className="brain">
              <span>✦</span>
            </div>

            <div className="floating-card card-two">
              <div className="mini-icon">✓</div>
              <div>
                <strong>Action extracted</strong>
                <small>Submit assignment</small>
              </div>
            </div>
          </div>
        </section>

        {message && (
          <div className="message">
            <span>✦</span>
            {message}
          </div>
        )}

        <section className="stats">
          <div className="stat-card">
            <div className="stat-icon">📋</div>
            <div>
              <span className="stat-number">{tasks.length}</span>
              <span className="stat-label">Total Tasks</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⏳</div>
            <div>
              <span className="stat-number">{pendingTasks.length}</span>
              <span className="stat-label">Pending</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✓</div>
            <div>
              <span className="stat-number">{completedTasks.length}</span>
              <span className="stat-label">Completed</span>
            </div>
          </div>
        </section>

        <section className="tasks-section">
          <div className="section-heading">
            <div>
              <span className="section-label">YOUR ACTIONS</span>
              <h3>Actionable tasks</h3>
            </div>

            {tasks.length > 0 && (
              <span className="task-count">
                {pendingTasks.length} pending
              </span>
            )}
          </div>

          {loading ? (
            <div className="empty-state">
              <div className="loader"></div>
              <h4>Loading your tasks...</h4>
              <p>Connecting to your LifeAdmin dashboard.</p>
            </div>
          ) : tasks.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✦</div>
              <h4>No tasks yet</h4>
              <p>
                Upload a screenshot or PDF and let LifeAdmin AI find the
                important things for you.
              </p>

              <button
                className="secondary-button"
                onClick={() => fileInputRef.current.click()}
              >
                Upload your first file
              </button>
            </div>
          ) : (
            <div className="task-list">
              {tasks.map((task) => (
                <article
                  className={`task-card ${
                    task.status === "completed" ? "completed" : ""
                  }`}
                  key={task.id}
                >
                  <div className="task-main">
                    <div className="task-check">
                      {task.status === "completed" ? "✓" : "•"}
                    </div>

                    <div className="task-content">
                      <div className="task-top">
                        <h4>{task.title}</h4>

                        <span
                          className={`priority ${getPriorityClass(
                            task.priority
                          )}`}
                        >
                          {task.priority}
                        </span>
                      </div>

                      <p>{task.reason}</p>

                      <div className="task-meta">
                        <span>📅 {task.date}</span>
                        <span>🕐 {task.time}</span>
                      </div>
                    </div>
                  </div>

                  <div className="task-actions">
                    {task.status !== "completed" && (
                      <button
                        className="complete-button"
                        onClick={() => completeTask(task.id)}
                      >
                        Complete
                      </button>
                    )}

                    <button
                      className="delete-button"
                      onClick={() => deleteTask(task.id)}
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="how-it-works">
          <div className="section-heading centered">
            <span className="section-label">HOW IT WORKS</span>
            <h3>From clutter to clarity</h3>
          </div>

          <div className="steps">
            <div className="step">
              <div className="step-number">01</div>
              <div className="step-icon">📤</div>
              <h4>Upload</h4>
              <p>Drop in a screenshot or PDF containing information.</p>
            </div>

            <div className="step-line"></div>

            <div className="step">
              <div className="step-number">02</div>
              <div className="step-icon">✦</div>
              <h4>Understand</h4>
              <p>AI identifies tasks, deadlines, events, and reminders.</p>
            </div>

            <div className="step-line"></div>

            <div className="step">
              <div className="step-number">03</div>
              <div className="step-icon">✓</div>
              <h4>Take action</h4>
              <p>See everything important in one organized dashboard.</p>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <strong>LifeAdmin AI</strong>
        <span>Turn life's clutter into actionable tasks.</span>
      </footer>
    </div>
  );
}

export default App;