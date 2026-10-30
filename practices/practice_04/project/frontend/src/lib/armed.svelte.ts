/** Подтверждение повторным нажатием: первое «взводит» кнопку на ms, второе — подтверждает. */
export class Armed {
  on = $state(false);
  #timer: ReturnType<typeof setTimeout> | undefined;
  #ms: number;

  constructor(ms = 4000) {
    this.#ms = ms;
  }

  /** true — это второе нажатие, действие можно выполнять. */
  press(): boolean {
    if (this.on) {
      this.reset();
      return true;
    }
    this.on = true;
    this.#timer = setTimeout(() => (this.on = false), this.#ms);
    return false;
  }

  reset() {
    clearTimeout(this.#timer);
    this.on = false;
  }
}
