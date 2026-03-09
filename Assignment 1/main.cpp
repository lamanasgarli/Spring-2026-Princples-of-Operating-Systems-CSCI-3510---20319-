#include <iostream>
#include <fstream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <string>
#include <chrono>
#include <random>
#include <atomic>
#include <sstream>
#include <algorithm>

using namespace std;

// ==========================================================
// CONFIGURATION
// ==========================================================

// Number of replicas
const int REPLICA_COUNT = 3;

// Total number of readers to create
const int TOTAL_READERS = 18;

// Number of times the writer will update all replicas
const int TOTAL_WRITES = 6;

// File names for replicas
const string replicaFiles[REPLICA_COUNT] = {
    "replica1.txt",
    "replica2.txt",
    "replica3.txt"
};

// Log file
const string LOG_FILE = "log.txt";

// ==========================================================
// SHARED DATA
// ==========================================================

// Mutex and condition variable for readers-writers synchronization
mutex rwMutex;
condition_variable cv;

// Mutex for logging and file content updates
mutex logMutex;

// Number of readers currently reading (total)
int activeReaders = 0;

// Number of writers waiting
int waitingWriters = 0;

// Whether writer is currently writing
bool writerActive = false;

// Number of readers currently reading each replica
int readersPerReplica[REPLICA_COUNT] = {0, 0, 0};

// In-memory content of replicas (mirrors actual files)
string replicaContents[REPLICA_COUNT];

// Used to give each write a version number
int writeVersion = 0;

// Random generator
random_device rd;
mt19937 gen(rd());

// ==========================================================
// UTILITY FUNCTIONS
// ==========================================================

// Random integer in range [low, high]
int getRandomInt(int low, int high) {
    uniform_int_distribution<> dist(low, high);
    return dist(gen);
}

// Sleep random milliseconds
void randomSleep(int lowMs, int highMs) {
    this_thread::sleep_for(chrono::milliseconds(getRandomInt(lowMs, highMs)));
}

// Write current in-memory contents to actual replica files
void writeReplicasToDisk() {
    for (int i = 0; i < REPLICA_COUNT; i++) {
        ofstream out(replicaFiles[i]);
        out << replicaContents[i];
        out.close();
    }
}

// Read a file from disk (used by readers for actual file access simulation)
string readFileFromDisk(const string& filename) {
    ifstream in(filename);
    stringstream buffer;
    buffer << in.rdbuf();
    return buffer.str();
}

// Create / reset files at program start
void initializeFiles() {
    string initialContent = "Initial shared content.\n";

    for (int i = 0; i < REPLICA_COUNT; i++) {
        replicaContents[i] = initialContent;
    }

    writeReplicasToDisk();

    ofstream logClear(LOG_FILE);
    logClear << "===== Readers-Writers Log Started =====\n";
    logClear.close();
}

// Log current system state after every read or write operation
void logState(const string& operation, int threadId, int replicaIndex, const string& fileContentSnapshot) {
    lock_guard<mutex> lock(logMutex);

    ofstream log(LOG_FILE, ios::app);

    log << "----------------------------------------\n";
    log << "Operation: " << operation << "\n";

    if (threadId != -1)
        log << "Thread ID: " << threadId << "\n";

    if (replicaIndex != -1)
        log << "Replica Accessed: replica" << (replicaIndex + 1) << ".txt\n";

    log << "Readers per replica: [";
    for (int i = 0; i < REPLICA_COUNT; i++) {
        log << readersPerReplica[i];
        if (i < REPLICA_COUNT - 1) log << ", ";
    }
    log << "]\n";

    log << "Writer active: " << (writerActive ? "YES" : "NO") << "\n";

    log << "Current replica contents:\n";
    for (int i = 0; i < REPLICA_COUNT; i++) {
        log << "replica" << (i + 1) << ".txt => " << replicaContents[i] << "\n";
    }

    if (!fileContentSnapshot.empty()) {
        log << "Content seen in this operation:\n";
        log << fileContentSnapshot << "\n";
    }

    log.close();
}

// Choose the replica with minimum active readers for load balancing
int chooseLeastLoadedReplica() {
    int minIndex = 0;
    for (int i = 1; i < REPLICA_COUNT; i++) {
        if (readersPerReplica[i] < readersPerReplica[minIndex]) {
            minIndex = i;
        }
    }
    return minIndex;
}

// ==========================================================
// READER FUNCTION
// ==========================================================

void reader(int readerId) {
    // Random arrival time
    randomSleep(100, 900);

    int chosenReplica = -1;

    // ---------------- ENTRY SECTION ----------------
    {
        unique_lock<mutex> lock(rwMutex);

        // Writer priority:
        // If a writer is active OR even waiting, new readers must wait.
        cv.wait(lock, []() {
            return !writerActive && waitingWriters == 0;
        });

        // Load balancing: choose the replica with the least active readers
        chosenReplica = chooseLeastLoadedReplica();

        // Register this reader
        activeReaders++;
        readersPerReplica[chosenReplica]++;
    }

    // ---------------- CRITICAL READING SECTION ----------------
    // Simulate reading from the selected replica
    string contentRead = readFileFromDisk(replicaFiles[chosenReplica]);

    // Simulate time spent reading
    randomSleep(200, 600);

    // Log read operation
    logState("READ", readerId, chosenReplica, contentRead);

    // ---------------- EXIT SECTION ----------------
    {
        unique_lock<mutex> lock(rwMutex);

        activeReaders--;
        readersPerReplica[chosenReplica]--;

        // If this was the last reader, wake waiting writer
        if (activeReaders == 0) {
            cv.notify_all();
        }
    }
}

// ==========================================================
// WRITER FUNCTION
// ==========================================================

void writer() {
    for (int i = 0; i < TOTAL_WRITES; i++) {
        // Writer sleeps random time before next write attempt
        randomSleep(500, 1200);

        // ---------------- ENTRY SECTION ----------------
        {
            unique_lock<mutex> lock(rwMutex);

            // Announce writer intention first
            waitingWriters++;

            // Wait until no readers and no writer active
            cv.wait(lock, []() {
                return activeReaders == 0 && !writerActive;
            });

            waitingWriters--;
            writerActive = true;
        }

        // ---------------- CRITICAL WRITING SECTION ----------------
        // Update all replicas "simultaneously" under writer-exclusive access
        writeVersion++;
        string newContent =
            "Updated by writer. Version = " + to_string(writeVersion) +
            ", Timestamp = " + to_string(
                chrono::duration_cast<chrono::milliseconds>(
                    chrono::system_clock::now().time_since_epoch()
                ).count()
            ) + "\n";

        {
            lock_guard<mutex> fileLock(logMutex);
            for (int r = 0; r < REPLICA_COUNT; r++) {
                replicaContents[r] = newContent;
            }
            writeReplicasToDisk();
        }

        // Simulate write duration
        randomSleep(300, 700);

        // Log write operation
        logState("WRITE", 0, -1, newContent);

        // ---------------- EXIT SECTION ----------------
        {
            unique_lock<mutex> lock(rwMutex);
            writerActive = false;
        }

        // Wake up all waiting threads
        cv.notify_all();
    }
}

// ==========================================================
// MAIN FUNCTION
// ==========================================================

int main() {
    initializeFiles();

    cout << "Starting Readers-Writers simulation with load balancing...\n";
    cout << "Replica files: replica1.txt, replica2.txt, replica3.txt\n";
    cout << "Log file: log.txt\n\n";

    // Create writer thread
    thread writerThread(writer);

    // Create reader threads
    vector<thread> readerThreads;
    for (int i = 1; i <= TOTAL_READERS; i++) {
        readerThreads.emplace_back(reader, i);
    }

    // Wait for all readers to finish
    for (auto& t : readerThreads) {
        t.join();
    }

    // Wait for writer to finish
    writerThread.join();

    cout << "Simulation completed successfully.\n";
    cout << "Check replica files and log.txt for results.\n";

    return 0;
}
